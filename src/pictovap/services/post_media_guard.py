"""Persistent integrity manifests for Pictovap-managed WordPress media blocks."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Dict, Iterable, List, Optional

from pictovap.utils.config import env_str, get_workspace_root


MANIFEST_VERSION = 1
_MEDIA_ID_RE = re.compile(r"wp-image-(\d+)", flags=re.IGNORECASE)
_HEADING_OR_IMAGE_RE = re.compile(
    r"(?P<heading><h(?P<level>[2-6])\b[^>]*>.*?</h(?P=level)>)"
    r"|(?P<image><!--\s+wp:image\b.*?<!--\s+/wp:image\s+-->)",
    flags=re.IGNORECASE | re.DOTALL,
)


def get_manifest_dir() -> Path:
    configured = env_str("PICTOVA_POST_MANIFEST_DIR")
    if configured:
        return Path(configured).expanduser()
    return get_workspace_root() / "data" / "post_media_manifests"


def manifest_path(site: str, post_id: int) -> Path:
    safe_site = re.sub(r"[^a-z0-9_-]+", "-", str(site).strip().lower()).strip("-")
    if not safe_site:
        raise ValueError("site is required")
    return get_manifest_dir() / f"{safe_site}-{int(post_id)}.json"


def extract_media_ids(content_raw: str) -> List[int]:
    return list(dict.fromkeys(int(value) for value in _MEDIA_ID_RE.findall(content_raw or "")))


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def _attribute(tag: str, name: str) -> str:
    match = re.search(
        rf"\b{re.escape(name)}\s*=\s*(['\"])(.*?)\1",
        tag,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return html.unescape(match.group(2)).strip() if match else ""


def media_items_from_content(
    content_raw: str,
    *,
    allowed_media_ids: Optional[Iterable[int]] = None,
) -> List[Dict[str, Any]]:
    """Extract reconstructable media items and their nearest heading anchor."""
    allowed = {int(value) for value in allowed_media_ids} if allowed_media_ids else None
    heading_text = ""
    heading_level = 0
    items: List[Dict[str, Any]] = []

    for match in _HEADING_OR_IMAGE_RE.finditer(content_raw or ""):
        heading = match.group("heading")
        if heading:
            heading_text = _strip_html(heading)
            heading_level = int(match.group("level") or 0)
            continue

        block = match.group("image") or ""
        media_match = _MEDIA_ID_RE.search(block)
        if not media_match:
            continue
        media_id = int(media_match.group(1))
        if allowed is not None and media_id not in allowed:
            continue

        image_tag_match = re.search(r"<img\b[^>]*>", block, flags=re.IGNORECASE | re.DOTALL)
        image_tag = image_tag_match.group(0) if image_tag_match else ""
        caption_match = re.search(
            r"<figcaption\b[^>]*>(.*?)</figcaption>",
            block,
            flags=re.IGNORECASE | re.DOTALL,
        )
        item = {
            "media_id": media_id,
            "url": _attribute(image_tag, "src"),
            "alt": _attribute(image_tag, "alt"),
            "caption": _strip_html(caption_match.group(1)) if caption_match else "",
            "heading": heading_text,
            "heading_level": heading_level,
        }
        if item["url"]:
            items.append(item)
    return items


def _normalize_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    media_id = int(item.get("media_id") or 0)
    url = str(item.get("url") or "").strip()
    if not media_id or not url:
        return None
    return {
        "media_id": media_id,
        "url": url,
        "alt": str(item.get("alt") or item.get("alt_text") or "").strip(),
        "caption": str(item.get("caption") or "").strip(),
        "heading": str(item.get("heading") or "").strip(),
        "heading_level": int(item.get("heading_level") or 0),
        "title": str(item.get("title") or "").strip(),
        "file": str(item.get("file") or "").strip(),
    }


def load_post_media_manifest(site: str, post_id: int) -> Optional[Dict[str, Any]]:
    path = manifest_path(site, post_id)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != MANIFEST_VERSION:
        raise ValueError(f"Unsupported post media manifest version: {payload.get('version')}")
    if payload.get("site") != site or int(payload.get("post_id") or 0) != int(post_id):
        raise ValueError(f"Post media manifest identity mismatch: {path}")
    return payload


def save_post_media_manifest(
    *,
    site: str,
    post_id: int,
    media_items: List[Dict[str, Any]],
    content_raw: str,
    post_modified: str = "",
) -> Dict[str, Any]:
    """Merge a successful attach into an atomic, reconstructable manifest."""
    existing = load_post_media_manifest(site, post_id) or {}
    existing_items = [
        normalized
        for raw in existing.get("media_items", [])
        if (normalized := _normalize_item(raw)) is not None
    ]
    incoming_items = [
        normalized
        for raw in media_items
        if (normalized := _normalize_item(raw)) is not None
    ]

    # The unanchored auto-media region is replaceable, not append-only.
    if any(not item["heading"] for item in incoming_items):
        existing_items = [item for item in existing_items if item["heading"]]

    merged: Dict[int, Dict[str, Any]] = {item["media_id"]: item for item in existing_items}
    merged.update({item["media_id"]: item for item in incoming_items})
    present_ids = set(extract_media_ids(content_raw))
    final_items = [item for media_id, item in merged.items() if media_id in present_ids]
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "version": MANIFEST_VERSION,
        "site": site,
        "post_id": int(post_id),
        "created_at": existing.get("created_at") or now,
        "updated_at": now,
        "post_modified": str(post_modified or ""),
        "content_sha256": hashlib.sha256((content_raw or "").encode("utf-8")).hexdigest(),
        "expected_media_ids": [item["media_id"] for item in final_items],
        "media_items": final_items,
    }

    path = manifest_path(site, post_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)
    return {**payload, "manifest_path": str(path)}


def assess_post_media(manifest: Dict[str, Any], content_raw: str) -> Dict[str, Any]:
    expected = [int(value) for value in manifest.get("expected_media_ids", [])]
    present = extract_media_ids(content_raw)
    present_set = set(present)
    missing = [media_id for media_id in expected if media_id not in present_set]
    state = "empty" if not expected else ("drift" if missing else "healthy")
    return {
        "state": state,
        "expected_media_ids": expected,
        "present_media_ids": [media_id for media_id in expected if media_id in present_set],
        "missing_media_ids": missing,
        "expected_count": len(expected),
        "present_count": len(expected) - len(missing),
    }


__all__ = [
    "assess_post_media",
    "extract_media_ids",
    "get_manifest_dir",
    "load_post_media_manifest",
    "manifest_path",
    "media_items_from_content",
    "save_post_media_manifest",
]
