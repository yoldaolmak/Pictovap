#!/usr/bin/env python3
"""
Pictovap WordPress uploader — REST API media upload and attachment.
"""

import requests
import json
import re
import html
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from pictova.core.primitives import CMSPlacement
from pictova.services.post_media_guard import (
    assess_post_media,
    load_post_media_manifest,
    manifest_path as post_media_manifest_path,
    media_items_from_content,
    save_post_media_manifest,
)
from pictova.utils.config import env_str, load_project_env

load_project_env()

try:
    from importlib.metadata import version as _dist_version

    _USER_AGENT = f"Pictovap-Media-Uploader/{_dist_version('pictovap')}"
except Exception:  # pragma: no cover - package metadata unavailable (source tree)
    _USER_AGENT = "Pictovap-Media-Uploader/dev"

AUTO_MEDIA_START = "<!-- yo:auto-media:start -->"
AUTO_MEDIA_END = "<!-- yo:auto-media:end -->"


class WordPressUploader:
    """Upload processed images to WordPress via REST API"""

    def __init__(self, site: str = "demo"):
        self.site = site
        prefix = f"{site.upper()}_" if site and site != "demo" else "WP_"

        # Default to the WP_ prefix if site-specific is not found. Note:
        # these must stay `None`, not placeholder strings -- a non-empty
        # fallback here would make the check below unreachable and let a
        # misconfigured deployment silently try to talk to a guessed
        # localhost server instead of failing clearly.
        self.base_url = env_str(f"{prefix}URL", env_str("WP_URL"))
        self.user = env_str(f"{prefix}USER", env_str("WP_USER"))
        self.password = env_str(f"{prefix}APP_PASSWORD", env_str("WP_APP_PASSWORD"))
        if not self.base_url or not self.user or not self.password:
            raise ValueError(
                f"Missing WordPress credentials for site: {site} "
                f"(expected {prefix}URL/{prefix}USER/{prefix}APP_PASSWORD "
                "or WP_URL/WP_USER/WP_APP_PASSWORD in .env)"
            )
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create authenticated session"""
        session = requests.Session()
        session.auth = (self.user, self.password)
        session.headers.update({
            "User-Agent": _USER_AGENT,
        })
        return session

    def upload_media(
        self,
        file_path: str,
        title: str,
        alt_text: str,
        description: str = "",
        caption: str = "",
    ) -> Dict:
        """Upload single image to WordPress media library.

        Returns:
            dict with media_id and details
        """
        file_p = Path(file_path)
        if not file_p.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        endpoint = f"{self.base_url}/wp-json/wp/v2/media"

        # Read file
        with open(file_path, "rb") as f:
            file_data = f.read()

        # Upload
        headers = {
            "Content-Disposition": f'attachment; filename="{file_p.name}"',
            "Content-Type": "image/webp",
        }

        try:
            resp = self.session.post(
                endpoint,
                data=file_data,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()

            media = resp.json()
            media_id = media["id"]

            # Update media metadata
            update_data = {
                "title": title,
                "description": description,
                "caption": caption,
                "alt_text": alt_text,
            }

            update_endpoint = f"{self.base_url}/wp-json/wp/v2/media/{media_id}"
            update_resp = self.session.post(
                update_endpoint,
                json=update_data,
                timeout=30,
            )
            update_resp.raise_for_status()

            return {
                "success": True,
                "media_id": media_id,
                "url": media.get("source_url", ""),
                "title": title,
                "alt_text": alt_text,
                "file": file_p.name,
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "file": file_p.name,
            }

    def attach_to_post(
        self,
        media_id: int,
        post_id: int,
    ) -> Dict:
        """Attach media to post (not as featured image)

        Args:
            media_id: WordPress media ID
            post_id: WordPress post ID

        Returns:
            dict with success status
        """
        endpoint = f"{self.base_url}/wp-json/wp/v2/media/{media_id}"

        try:
            resp = self.session.post(
                endpoint,
                json={"post": post_id},
                timeout=30,
            )
            resp.raise_for_status()

            return {
                "success": True,
                "media_id": media_id,
                "post_id": post_id,
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "media_id": media_id,
            }

    def fetch_post_context(self, post_id: int) -> Dict:
        endpoint = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}?context=edit"
        try:
            resp = self.session.get(endpoint, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            excerpt_raw = _extract_post_field(data.get("excerpt", {}), prefer="raw")
            content_raw = _extract_post_field(data.get("content", {}), prefer="raw")
            return {
                "id": post_id,
                "status": str(data.get("status", "")).strip(),
                "modified": str(data.get("modified", "")).strip(),
                "modified_gmt": str(data.get("modified_gmt", "")).strip(),
                "title": html.unescape(data.get("title", {}).get("rendered", "")).strip(),
                "slug": str(data.get("slug", "")).strip(),
                "excerpt": _strip_html(excerpt_raw),
                "content": _strip_html(content_raw)[:2500],
                "content_raw": content_raw,
                "available_headings": _extract_available_headings(content_raw),
            }
        except requests.exceptions.RequestException:
            return {}

    # ------------------------------------------------------------------
    # Public interface (CMSAdapter)
    # ------------------------------------------------------------------

    def place(self, placement: CMSPlacement) -> Dict[str, Any]:
        """Execute a CMS-agnostic placement plan against this WordPress site.

        `placement.article_id` is interpreted as the numeric WordPress post
        ID. Each `PlacementInstruction.output_path` must point to a real,
        already processed image file on disk.

        Internally delegates to `upload_images_batch`, which uploads every
        image, attaches it to the post, and inserts a Gutenberg image block
        at `target_section` (matched by heading text) — this is the same
        path used by the production WordPress integration, so placement
        here honors `target_section` in a way the Ghost/Strapi adapters
        currently do not.
        """
        try:
            post_id = int(placement.article_id)
        except (TypeError, ValueError):
            return {
                "placed": [],
                "failed": [],
                "warnings": [
                    f"CMSPlacement.article_id={placement.article_id!r} is not a valid WordPress post ID"
                ],
            }

        slot_by_filename = {Path(instr.output_path).name: instr.slot_id for instr in placement.placements}
        metadata_dict = {
            instr.output_path: {
                "title": instr.slot_id,
                "alt": instr.alt_text,
                "caption": instr.caption,
                "heading": instr.target_section,
            }
            for instr in placement.placements
        }

        batch_result = upload_images_batch(
            image_files=list(metadata_dict.keys()),
            metadata_dict=metadata_dict,
            post_id=post_id,
            site=self.site,
        )

        placed: List[Dict[str, Any]] = []
        failed: List[Dict[str, Any]] = list(batch_result.get("failed", []))
        for item in batch_result.get("uploaded", []):
            entry = {
                "slot_id": slot_by_filename.get(item.get("file", ""), item.get("title", "")),
                "media_id": item.get("media_id"),
                "url": item.get("url", ""),
            }
            if item.get("attach_error"):
                failed.append({**entry, "error": item["attach_error"]})
            else:
                placed.append(entry)

        warnings: List[str] = []
        guard = batch_result.get("media_guard", {})
        if guard.get("status") in {"drift", "failed"}:
            warnings.append(f"media integrity guard reported status={guard.get('status')!r}")
        content_result = batch_result.get("content_update", {})
        if content_result and not content_result.get("success"):
            warnings.append(f"post content update failed: {content_result.get('error', 'unknown error')}")

        return {"placed": placed, "failed": failed, "warnings": warnings}

    def append_media_to_post_content(
        self,
        post_id: int,
        media_items: List[Dict],
        *,
        allow_manifest_repair: bool = False,
    ) -> Dict:
        post = self.fetch_post_context(post_id)
        if not post:
            return {"success": False, "error": "Post context could not be loaded"}

        current_content = post.get("content_raw", "") or ""
        original_content = current_content
        try:
            manifest = load_post_media_manifest(self.site, post_id)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return {
                "success": False,
                "code": "media_manifest_invalid",
                "error": str(exc),
            }
        if manifest and not allow_manifest_repair:
            integrity = assess_post_media(manifest, current_content)
            if integrity["state"] == "drift":
                return {
                    "success": False,
                    "code": "media_manifest_drift",
                    "error": "Pictovap-managed media blocks are missing; run guard --repair before attaching new media",
                    **integrity,
                }

        current_content, removed_broken = self._remove_broken_local_image_blocks(current_content)
        has_unanchored_items = any(not str(item.get("heading", "") or "").strip() for item in media_items)
        if has_unanchored_items:
            current_content = _remove_auto_media_region(current_content)

        from collections import defaultdict

        groups = defaultdict(list)
        for item in media_items:
            heading_text = str(item.get("heading", "") or "").strip()
            heading_level = int(item.get("heading_level", 0) or 0)
            groups[(heading_text, heading_level)].append(item)

        auto_blocks: list[str] = []
        inserted = 0

        for (heading_text, heading_level), items in groups.items():
            valid_items = []
            for item in items:
                media_id = item.get("media_id")
                url = item.get("url", "")
                if not media_id or not url:
                    continue
                marker = f"wp-image-{media_id}"
                if marker in current_content or url in current_content:
                    continue
                valid_items.append(item)

            if not valid_items:
                continue

            if len(valid_items) == 1:
                # Single wp:image
                item = valid_items[0]
                media_id = item.get("media_id")
                url = item.get("url", "")
                alt_text = _escape_attr(item.get("alt", ""))
                caption = _escape_html(item.get("caption", ""))
                block = (
                    f'<!-- wp:image {{"id":{media_id},"sizeSlug":"full","linkDestination":"none"}} -->\n'
                    f'<figure class="wp-block-image size-full"><img src="{url}" alt="{alt_text}" '
                    f'class="wp-image-{media_id}"/>'
                )
                if caption:
                    block += f'<figcaption class="wp-element-caption">{caption}</figcaption>'
                block += "</figure>\n<!-- /wp:image -->"
            else:
                # Group wp:gallery
                block = '<!-- wp:gallery {"linkTo":"none"} -->\n'
                block += '<figure class="wp-block-gallery has-nested-images columns-default is-cropped">\n'
                for item in valid_items:
                    media_id = item.get("media_id")
                    url = item.get("url", "")
                    alt_text = _escape_attr(item.get("alt", ""))
                    caption = _escape_html(item.get("caption", ""))
                    block += (
                        f'<!-- wp:image {{"id":{media_id},"sizeSlug":"large","linkDestination":"none"}} -->\n'
                        f'<figure class="wp-block-image size-large"><img src="{url}" alt="{alt_text}" '
                        f'class="wp-image-{media_id}"/>'
                    )
                    if caption:
                        block += f'<figcaption class="wp-element-caption">{caption}</figcaption>'
                    block += "</figure>\n<!-- /wp:image -->\n"
                block += '</figure>\n<!-- /wp:gallery -->'

            if heading_text:
                updated_content = _insert_block_after_heading(
                    current_content,
                    heading_text=heading_text,
                    block_html=block,
                    heading_level=heading_level or None,
                )
                if updated_content != current_content:
                    current_content = updated_content
                    inserted += len(valid_items)
                    continue

            auto_blocks.append(block)
            inserted += len(valid_items)

        if not auto_blocks:
            if current_content != original_content or removed_broken:
                return self._commit_post_content(
                    post_id=post_id,
                    original_content=original_content,
                    original_modified=post.get("modified", ""),
                    new_content=current_content,
                    media_items=media_items,
                    inserted=inserted,
                    removed_broken=removed_broken,
                )
            return self._record_verified_media(
                post_id=post_id,
                post=post,
                media_items=media_items,
                updated=False,
                inserted=0,
                removed_broken=removed_broken,
            )

        combined_blocks = AUTO_MEDIA_START + "\n" + "\n\n".join(auto_blocks) + "\n" + AUTO_MEDIA_END
        new_content = _insert_before_first_h2(current_content, combined_blocks)
        return self._commit_post_content(
            post_id=post_id,
            original_content=original_content,
            original_modified=post.get("modified", ""),
            new_content=new_content,
            media_items=media_items,
            inserted=inserted,
            removed_broken=removed_broken,
        )

    def _commit_post_content(
        self,
        *,
        post_id: int,
        original_content: str,
        original_modified: str,
        new_content: str,
        media_items: List[Dict],
        inserted: int,
        removed_broken: int,
    ) -> Dict:
        """Optimistic write followed by a read-after-write integrity check."""
        latest = self.fetch_post_context(post_id)
        if not latest:
            return {"success": False, "error": "Post could not be reloaded before update"}
        if (latest.get("content_raw", "") or "") != original_content:
            return {
                "success": False,
                "code": "post_content_conflict",
                "error": "Post changed while Pictovap was preparing media blocks; no content was overwritten",
                "expected_modified": original_modified,
                "current_modified": latest.get("modified", ""),
            }

        endpoint = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
        try:
            resp = self.session.post(
                endpoint,
                json={"content": new_content},
                timeout=30,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as exc:
            return {"success": False, "error": str(exc)}

        verified = self.fetch_post_context(post_id)
        if not verified:
            return {"success": False, "error": "Post update could not be verified"}
        return self._record_verified_media(
            post_id=post_id,
            post=verified,
            media_items=media_items,
            updated=True,
            inserted=inserted,
            removed_broken=removed_broken,
        )

    def _record_verified_media(
        self,
        *,
        post_id: int,
        post: Dict,
        media_items: List[Dict],
        updated: bool,
        inserted: int,
        removed_broken: int,
    ) -> Dict:
        expected_ids = [int(item.get("media_id") or 0) for item in media_items if item.get("media_id")]
        if not expected_ids:
            return {
                "success": True,
                "updated": updated,
                "inserted": inserted,
                "removed_broken": removed_broken,
            }

        content_raw = post.get("content_raw", "") or ""
        present_ids = {int(value) for value in re.findall(r"wp-image-(\d+)", content_raw)}
        missing_ids = [media_id for media_id in expected_ids if media_id not in present_ids]
        if missing_ids:
            return {
                "success": False,
                "code": "post_update_verification_failed",
                "error": "WordPress accepted the update but expected media blocks are missing",
                "missing_media_ids": missing_ids,
            }

        try:
            manifest = save_post_media_manifest(
                site=self.site,
                post_id=post_id,
                media_items=media_items,
                content_raw=content_raw,
                post_modified=post.get("modified", ""),
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return {
                "success": False,
                "code": "media_manifest_write_failed",
                "error": str(exc),
            }
        return {
            "success": True,
            "updated": updated,
            "inserted": inserted,
            "removed_broken": removed_broken,
            "manifest_path": manifest["manifest_path"],
            "expected_media_ids": manifest["expected_media_ids"],
        }

    def guard_post_media(
        self,
        post_id: int,
        *,
        repair: bool = False,
        adopt: bool = False,
        media_ids: Optional[List[int]] = None,
    ) -> Dict:
        """Check, adopt, or safely reconstruct Pictovap-managed media blocks."""
        post = self.fetch_post_context(post_id)
        if not post:
            return {"command": "guard", "status": "failed", "error": "Post context could not be loaded"}

        try:
            manifest = load_post_media_manifest(self.site, post_id)
            if adopt:
                items = media_items_from_content(
                    post.get("content_raw", "") or "",
                    allowed_media_ids=media_ids,
                )
                if not items:
                    return {
                        "command": "guard",
                        "status": "untracked",
                        "state": "untracked",
                        "post_id": post_id,
                        "error": "No media blocks were available to adopt",
                    }
                manifest = save_post_media_manifest(
                    site=self.site,
                    post_id=post_id,
                    media_items=items,
                    content_raw=post.get("content_raw", "") or "",
                    post_modified=post.get("modified", ""),
                )
            if manifest is None:
                return {
                    "command": "guard",
                    "status": "untracked",
                    "state": "untracked",
                    "site": self.site,
                    "post_id": post_id,
                }

            integrity = assess_post_media(manifest, post.get("content_raw", "") or "")
            repaired = False
            if integrity["state"] == "drift" and repair:
                result = self.append_media_to_post_content(
                    post_id,
                    manifest.get("media_items", []),
                    allow_manifest_repair=True,
                )
                if not result.get("success"):
                    return {
                        "command": "guard",
                        "status": "failed",
                        "state": "drift",
                        "site": self.site,
                        "post_id": post_id,
                        "repair": result,
                        **integrity,
                    }
                post = self.fetch_post_context(post_id)
                manifest = load_post_media_manifest(self.site, post_id) or manifest
                integrity = assess_post_media(manifest, post.get("content_raw", "") or "")
                repaired = integrity["state"] == "healthy"

            status = "success" if integrity["state"] in {"healthy", "empty"} else "drift"
            return {
                "command": "guard",
                "status": status,
                "state": integrity["state"],
                "site": self.site,
                "post_id": post_id,
                "repaired": repaired,
                "manifest_path": str(post_media_manifest_path(self.site, post_id)),
                **integrity,
            }
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return {
                "command": "guard",
                "status": "failed",
                "state": "invalid",
                "site": self.site,
                "post_id": post_id,
                "error": str(exc),
            }

    def cleanup_broken_media_from_post(self, post_id: int) -> Dict:
        post = self.fetch_post_context(post_id)
        if not post:
            return {"success": False, "error": "Post context could not be loaded"}
        current_content = post.get("content_raw", "") or ""
        cleaned_content, removed_broken = self._remove_broken_local_image_blocks(current_content)
        cleaned_content = _remove_auto_media_region(cleaned_content)
        if removed_broken == 0 and cleaned_content == current_content:
            return {"success": True, "updated": False, "removed_broken": 0}
        endpoint = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
        try:
            resp = self.session.post(
                endpoint,
                json={"content": cleaned_content},
                timeout=30,
            )
            resp.raise_for_status()
            return {"success": True, "updated": True, "removed_broken": removed_broken}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def _remove_broken_local_image_blocks(self, content: str) -> tuple[str, int]:
        removed = 0

        def replace_block(match: re.Match[str]) -> str:
            nonlocal removed
            block = match.group(0)
            src_match = re.search(r'<img[^>]+src="([^"]+)"', block, flags=re.I)
            if not src_match:
                return block
            src = src_match.group(1)
            if not src.startswith(self.base_url + "/wp-content/uploads/"):
                return block
            try:
                resp = self.session.get(src, timeout=15, allow_redirects=True)
                if resp.status_code == 404:
                    removed += 1
                    return ""
            except requests.exceptions.RequestException:
                return block
            return block

        cleaned = re.sub(
            r"<!-- wp:image\b.*?<!-- /wp:image -->\s*",
            replace_block,
            content,
            flags=re.S,
        )
        return cleaned.strip() + ("\n" if cleaned.strip() else ""), removed


def _strip_html(value: str) -> str:
    text = re.sub(r"<style[^>]*>.*?</style>", " ", value, flags=re.S | re.I)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def fetch_post_context(post_id: int, site: str = "demo") -> Dict:
    uploader = WordPressUploader(site=site)
    return uploader.fetch_post_context(post_id)


def _extract_post_field(value: object, *, prefer: str = "rendered") -> str:
    if isinstance(value, dict):
        preferred = value.get(prefer)
        if isinstance(preferred, str):
            return preferred
        rendered = value.get("rendered")
        if isinstance(rendered, str):
            return rendered
    return str(value or "")


def _escape_attr(value: str) -> str:
    return html.escape(str(value or ""), quote=True)


def _escape_html(value: str) -> str:
    return html.escape(str(value or ""))


def _insert_before_first_h2(content: str, block_html: str) -> str:
    block_match = re.search(
        r"<!-- wp:heading(?:\s+\{.*?\})? -->\s*<h2\b[^>]*>.*?</h2>\s*<!-- /wp:heading -->",
        content,
        flags=re.S | re.I,
    )
    if block_match:
        insert_at = block_match.start()
    else:
        match = re.search(r"<h2\b[^>]*>", content, flags=re.I)
        if not match:
            return content.rstrip() + "\n\n" + block_html + "\n"
        insert_at = match.start()
    prefix = content[:insert_at].rstrip()
    suffix = content[insert_at:].lstrip()
    return prefix + "\n\n" + block_html + "\n\n" + suffix


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_strip_html(value))).strip().lower()


def _insert_block_after_heading(
    content: str,
    *,
    heading_text: str,
    block_html: str,
    heading_level: Optional[int] = None,
) -> str:
    def _inside_code_like_block(full: str, start: int, end: int) -> bool:
        containers = [
            re.compile(r"<!-- wp:code(?:\s+\{.*?\})? -->.*?<!-- /wp:code -->", flags=re.S | re.I),
            re.compile(r"<!-- wp:preformatted(?:\s+\{.*?\})? -->.*?<!-- /wp:preformatted -->", flags=re.S | re.I),
            re.compile(r"<!-- wp:html(?:\s+\{.*?\})? -->.*?<!-- /wp:html -->", flags=re.S | re.I),
            re.compile(r"<pre\b[^>]*>.*?</pre>", flags=re.S | re.I),
        ]
        for container in containers:
            for block in container.finditer(full):
                if start >= block.start() and end <= block.end():
                    return True
        return False

    pattern = re.compile(
        r"<!-- wp:heading(?:\s+\{.*?\})? -->\s*<h(?P<level>[1-6])\b[^>]*>.*?</h(?P=level)>\s*<!-- /wp:heading -->",
        flags=re.S | re.I,
    )
    target = _normalize_text(heading_text)

    for match in pattern.finditer(content):
        level = int(match.group("level"))
        if heading_level and level != heading_level:
            continue

        heading_block = match.group(0)
        if target not in _normalize_text(heading_block):
            continue
        if _inside_code_like_block(content, match.start(), match.end()):
            continue

        # Guardrail: skip insertion when an image already exists directly
        # above/below the heading, or with only one paragraph gap.
        before = content[: match.start()]
        after = content[match.end():]
        has_nearby_image_before = re.search(
            r"<!-- wp:image\b.*?<!-- /wp:image -->\s*(?:<!-- wp:paragraph(?:\s+\{.*?\})? -->.*?<!-- /wp:paragraph -->\s*)?$",
            before,
            flags=re.S | re.I,
        )
        has_nearby_image_after = re.match(
            r"\s*(?:<!-- wp:paragraph(?:\s+\{.*?\})? -->.*?<!-- /wp:paragraph -->\s*)?<!-- wp:image\b",
            after,
            flags=re.S | re.I,
        )
        if has_nearby_image_before or has_nearby_image_after:
            continue

        insert_at = match.end()
        prefix = content[:insert_at].rstrip()
        suffix = content[insert_at:].lstrip()
        return prefix + "\n\n" + block_html + "\n\n" + suffix

    return content


def _extract_available_headings(content: str) -> list[dict]:
    """Return H2/H3 Gutenberg headings that don't already have an image nearby."""
    heading_pattern = re.compile(
        r"<!-- wp:heading(?:\s+\{.*?\})? -->\s*<h(?P<level>[2-3])\b[^>]*>(?P<inner>.*?)</h(?P=level)>\s*<!-- /wp:heading -->",
        flags=re.S | re.I,
    )
    results = []
    for match in heading_pattern.finditer(content):
        level = int(match.group("level"))
        text = _strip_html(match.group("inner")).strip()
        if not text:
            continue
        before = content[: match.start()]
        after = content[match.end():]
        # Reuse the same proximity guards used in _insert_block_after_heading
        has_image_before = re.search(
            r"<!-- wp:image\b.*?<!-- /wp:image -->\s*(?:<!-- wp:paragraph(?:\s+\{.*?\})? -->.*?<!-- /wp:paragraph -->\s*)?$",
            before,
            flags=re.S | re.I,
        )
        has_image_after = re.match(
            r"\s*(?:<!-- wp:paragraph(?:\s+\{.*?\})? -->.*?<!-- /wp:paragraph -->\s*)?<!-- wp:image\b",
            after,
            flags=re.S | re.I,
        )
        if has_image_before or has_image_after:
            continue
        results.append({"text": text, "level": level})
    return results


def _remove_auto_media_region(content: str) -> str:
    cleaned = re.sub(
        re.escape(AUTO_MEDIA_START) + r".*?" + re.escape(AUTO_MEDIA_END) + r"\s*",
        "",
        content,
        flags=re.S,
    )
    return cleaned.strip() + ("\n" if cleaned.strip() else "")


def upload_images_batch(
    image_files: List[str],
    metadata_dict: Dict,  # filepath → {alt, title, caption, description}
    post_id: int,
    site: str = "demo",
) -> Dict:
    """Upload multiple processed images and attach to post

    Args:
        image_files: list of WebP file paths
        metadata_dict: metadata per file
        post_id: target WordPress post ID
        site: site name prefix for env-based credentials (e.g. "myblog"
            reads MYBLOG_URL / MYBLOG_USER / MYBLOG_APP_PASSWORD;
            "demo" falls back to WP_*)

    Returns:
        dict with results
    """
    uploader = WordPressUploader(site=site)
    results = {
        "site": site,
        "post_id": post_id,
        "uploaded": [],
        "failed": [],
    }

    guard = uploader.guard_post_media(post_id)
    results["media_guard"] = guard
    if guard.get("status") in {"drift", "failed"}:
        results["failed"].append({
            "error": "Post media integrity check failed before upload",
            "guard": guard,
        })
        return results

    for i, file_path in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] Uploading: {Path(file_path).name}")

        meta = metadata_dict.get(file_path, {})
        if not meta:
            print("  ✗ No metadata found", file=sys.stderr)
            results["failed"].append({
                "file": file_path,
                "error": "No metadata",
            })
            continue

        # Upload media
        upload_result = uploader.upload_media(
            file_path=file_path,
            title=meta.get("title", "Image"),
            alt_text=meta.get("alt", ""),
            description=meta.get("description", ""),
            caption=meta.get("caption", ""),
        )

        if not upload_result["success"]:
            print(f"  ✗ Upload failed: {upload_result['error']}")
            results["failed"].append({
                "file": file_path,
                "error": upload_result["error"],
            })
            continue

        media_id = upload_result["media_id"]
        print(f"  ✓ Uploaded: ID {media_id}", file=sys.stderr)

        # Attach to post
        attach_result = uploader.attach_to_post(
            media_id=media_id,
            post_id=post_id,
        )

        if attach_result["success"]:
            print(f"  ✓ Attached to post {post_id}")
            results["uploaded"].append({
                "file": Path(file_path).name,
                "media_id": media_id,
                "post_id": post_id,
                "title": meta.get("title"),
                "alt": meta.get("alt"),
                "caption": meta.get("caption"),
                "heading": meta.get("heading"),
                "heading_level": meta.get("heading_level"),
                "url": upload_result.get("url", ""),
            })
        else:
            print(f"  ⚠️  Upload OK but attach failed: {attach_result['error']}")
            results["uploaded"].append({
                "file": Path(file_path).name,
                "media_id": media_id,
                "attach_error": attach_result["error"],
                "caption": meta.get("caption"),
                "title": meta.get("title"),
                "alt": meta.get("alt"),
                "heading": meta.get("heading"),
                "heading_level": meta.get("heading_level"),
                "url": upload_result.get("url", ""),
            })

    content_result = uploader.append_media_to_post_content(post_id, results["uploaded"])
    results["content_update"] = content_result
    if content_result.get("success") and content_result.get("updated"):
        print(f"\n✓ Post content updated: {content_result.get('inserted', 0)} image block added")
    elif not content_result.get("success"):
        print(f"\n⚠️  Post content update failed: {content_result.get('error', 'unknown error')}")

    return results


if __name__ == "__main__":
    # Test authentication
    uploader = WordPressUploader(site="demo")
    print(f"✓ Connected to {uploader.base_url}")
    print(f"  User: {uploader.user}")
    print("\nReady for image uploads")
