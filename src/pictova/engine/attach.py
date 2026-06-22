"""Canonical attach orchestration helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import Any, Dict, Tuple

from src.main import YOOrchestrator
from src.core.media_publish import build_publish_slug_candidates, embed_metadata, ensure_publish_path, ensure_unique_slug
from src.pictova.profiles.yoldaolmak import apply_environment
from src.pictova.engine.metadata import build_native_metadata_map
from src.pictova.engine.quality import quality_gate_native_batch
from src.pictova.providers.wordpress import fetch_post_context
from src.pictova.engine.processor import process_selected_images
from src.pictova.engine.publisher import publish_processed_images
from src.pictova.engine.selector import resolve_source_images
from src.pictova.engine.vision_chain import download_icloud_photo


def _photo_index_stats() -> dict:
    """Visual memory DB özet istatistikleri."""
    import sqlite3 as _sq
    try:
        from src.pictova.config import get_visual_memory_db_path
        db = get_visual_memory_db_path()
        con = _sq.connect(str(db))
        row = con.execute("""
            SELECT
              COUNT(*) AS total,
              SUM(CASE WHEN source_path != '' THEN 1 ELSE 0 END) AS local_count,
              SUM(CASE WHEN source_path  = '' THEN 1 ELSE 0 END) AS icloud_count,
              SUM(CASE WHEN vision_scan_status = 'done' THEN 1 ELSE 0 END) AS scanned
            FROM asset_index WHERE is_personal = 0
        """).fetchone()
        con.close()
        return {"total": row[0], "local": row[1], "icloud": row[2], "vision_scanned": row[3]}
    except Exception as exc:
        return {"error": str(exc)}


def resolve_icloud_files(files: list[str], warnings: list[str]) -> list[str]:
    """iCloud UUID (icloud://UUID) dosyalarını indirip lokal path ile değiştirir."""
    resolved = []
    for f in files:
        if f.startswith("icloud://"):
            uuid = f.removeprefix("icloud://")
            try:
                local = download_icloud_photo(uuid)
                resolved.append(local)
            except Exception as exc:
                warnings.append(f"iCloud indir başarısız ({uuid[:8]}): {exc}")
        else:
            resolved.append(f)
    return resolved


def summarize_post_context(post_context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": post_context.get("id"),
        "title": post_context.get("title", ""),
        "slug": post_context.get("slug", ""),
    }


_SLUG_GENERIC = {
    "gezilecek", "yerler", "yerleri", "gezi", "rehberi", "rehber",
    "nerede", "nasil", "nasil-gidilir", "seyahat", "travel", "guide",
    "rota", "rotasi", "rotalar", "detayli", "guncel", "notlari",
    "ve", "ile", "icin", "the", "and", "bir",
}


def derive_location_query(post_context: Dict[str, Any]) -> str:
    """Slug'dan ilk 1-2 anlamlı destinasyon tokenini çıkar.

    Tam başlık AND-logic semantic aramayı kırar (8+ token → hiçbir şey eşleşmez).
    Sadece destinasyon adı yeterli: 'sinop-gezilecek-yerler' → 'sinop'.
    """
    slug = str(post_context.get("slug") or "").strip()
    tokens = [
        t for t in slug.split("-")
        if t and t not in _SLUG_GENERIC and len(t) >= 3 and not t.isdigit()
    ]
    if tokens:
        return " ".join(tokens[:2])
    title = str(post_context.get("title") or "").strip()
    return re.sub(r"\s+", " ", title).strip()


def build_failed_attach_result(
    *,
    site: str,
    post_id: Any,
    request: Dict[str, Any],
    post_context: Dict[str, Any],
    constraints: Dict[str, Any],
    warning: str,
) -> Dict[str, Any]:
    return {
        "command": "attach",
        "site": site,
        "post_id": post_id,
        "request": request,
        "post_context": summarize_post_context(post_context),
        "status": "failed",
        "selected_assets": [],
        "rejected_assets": [],
        "uploaded_media_ids": [],
        "inserted_blocks": 0,
        "uploaded": [],
        "failed_uploads": [],
        "constraints": constraints,
        "warnings": [warning],
        "duration_ms": 0,
        "raw": {},
    }


def normalize_attach_result(
    raw: Dict[str, Any],
    *,
    constraints: Dict[str, Any],
    duration_ms: int,
    request: Dict[str, Any],
    post_context: Dict[str, Any],
) -> Dict[str, Any]:
    upload_complete = raw.get("steps", {}).get("upload_complete", {})
    uploaded = upload_complete.get("uploaded", [])
    content_update = upload_complete.get("content_update", {})
    warning = raw.get("warning") or raw.get("error")
    quality_gate = raw.get("steps", {}).get("quality_gate", {})
    return {
        "command": "attach",
        "site": raw.get("site"),
        "post_id": raw.get("post_id"),
        "request": request,
        "post_context": summarize_post_context(post_context),
        "status": raw.get("status"),
        "selected_assets": raw.get("steps", {}).get("images_loaded", {}).get("files", []),
        "rejected_assets": quality_gate.get("blocked", []),
        "uploaded_media_ids": [item.get("media_id") for item in uploaded if item.get("media_id")],
        "inserted_blocks": content_update.get("inserted", 0),
        "uploaded": uploaded,
        "failed_uploads": upload_complete.get("failed", []),
        "constraints": constraints,
        "warnings": [warning] if warning else [],
        "duration_ms": duration_ms,
        "raw": raw,
    }


def prepare_attach_request(**kwargs: Any) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    site = kwargs.get("site", "yoldaolmak")
    if site == "yoldaolmak":
        apply_environment()

    request = dict(kwargs)
    post_id = request.get("post_id")
    post_context = {}
    if post_id:
        try:
            post_context = fetch_post_context(post_id, site=site) or {}
        except Exception:
            post_context = {}

    if request.get("source") == "semantic" and not request.get("location_query"):
        request["location_query"] = derive_location_query(post_context)

    constraints = {
        "language": request.pop("language", "tr"),
        "people_first": bool(request.pop("people_first", False)),
    }
    if constraints["people_first"] and not request.get("content_filter"):
        request["content_filter"] = "insan"

    return request, post_context, constraints


def validate_attach_request(
    *,
    site: str,
    request: Dict[str, Any],
    post_context: Dict[str, Any],
    constraints: Dict[str, Any],
) -> Dict[str, Any] | None:
    post_id = request.get("post_id")
    source = request.get("source", "semantic")
    if source == "semantic" and not request.get("location_query"):
        return build_failed_attach_result(
            site=site,
            post_id=post_id,
            request=request,
            post_context=post_context,
            constraints=constraints,
            warning="location_query could not be derived; provide --location-query or ensure the post has a usable title/slug",
        )
    if source == "unsplash" and not request.get("query"):
        return build_failed_attach_result(
            site=site,
            post_id=post_id,
            request=request,
            post_context=post_context,
            constraints=constraints,
            warning="query is required when source=unsplash",
        )
    if not post_id:
        return build_failed_attach_result(
            site=site,
            post_id=post_id,
            request=request,
            post_context=post_context,
            constraints=constraints,
            warning="post_id is required for attach",
        )
    return None


def execute_legacy_attach(
    *,
    site: str,
    request: Dict[str, Any],
    post_context: Dict[str, Any],
    constraints: Dict[str, Any],
) -> Dict[str, Any]:
    started = datetime.utcnow()
    orchestrator = YOOrchestrator()
    raw = orchestrator.run_pipeline(**request)
    duration_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
    return normalize_attach_result(
        raw,
        constraints=constraints,
        duration_ms=duration_ms,
        request=request,
        post_context=post_context,
    )


def build_attach_plan(
    *,
    site: str,
    request: Dict[str, Any],
    post_context: Dict[str, Any],
    constraints: Dict[str, Any],
) -> Dict[str, Any]:
    failure = validate_attach_request(
        site=site,
        request=request,
        post_context=post_context,
        constraints=constraints,
    )
    if failure:
        failure["command"] = "plan"
        return failure

    selection = resolve_source_images(
        source=request.get("source", "semantic"),
        count=request.get("count"),
        name=request.get("name"),
        query=request.get("query"),
        location_query=request.get("location_query"),
        content_filter=request.get("content_filter"),
        post_context=post_context,
    )
    return {
        "command": "plan",
        "site": site,
        "post_id": request.get("post_id"),
        "request": request,
        "post_context": summarize_post_context(post_context),
        "constraints": constraints,
        "status": "success",
        "selection": selection,
        "photo_index_stats": _photo_index_stats(),
        "warnings": [],
    }


def build_process_result(
    *,
    site: str,
    request: Dict[str, Any],
    post_context: Dict[str, Any],
    constraints: Dict[str, Any],
) -> Dict[str, Any]:
    failure = validate_attach_request(
        site=site,
        request=request,
        post_context=post_context,
        constraints=constraints,
    )
    if failure:
        failure["command"] = "process"
        return failure

    selection = resolve_source_images(
        source=request.get("source", "semantic"),
        count=request.get("count"),
        name=request.get("name"),
        query=request.get("query"),
        location_query=request.get("location_query"),
        content_filter=request.get("content_filter"),
        post_context=post_context,
    )
    _warnings: list[str] = []
    _files = resolve_icloud_files(selection.get("files", []), _warnings)
    processed = process_selected_images(_files)
    return {
        "command": "process",
        "site": site,
        "post_id": request.get("post_id"),
        "request": request,
        "post_context": summarize_post_context(post_context),
        "constraints": constraints,
        "status": "success",
        "selection": selection,
        "processed_images": processed.get("processed_images", []),
        "panoramic_images": processed.get("panoramic_images", {}),
        "work_dir": processed.get("work_dir"),
        "warnings": [],
    }


def finalize_publish_assets(
    *,
    processed_images: list[str],
    metadata_dict: Dict[str, Dict[str, Any]],
    processed_details: Dict[str, Dict[str, Any]],
    post_context: Dict[str, Any],
    work_dir: str | None,
) -> tuple[list[str], Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    used_slugs: set[str] = set()
    finalized_files: list[str] = []
    finalized_metadata: Dict[str, Dict[str, Any]] = {}
    finalized_details: Dict[str, Dict[str, Any]] = {}
    target_dir = Path(work_dir) if work_dir else (Path(processed_images[0]).parent if processed_images else Path("/tmp"))

    for file in processed_images:
        meta = dict(metadata_dict.get(file, {}))
        process_info = dict(processed_details.get(file, {}))
        slug_source_path = str(process_info.get("input") or file)
        slug_candidates = build_publish_slug_candidates(meta, post_context, slug_source_path)
        candidate_slug = ensure_unique_slug(slug_candidates[0], used_slugs)
        for slug in slug_candidates:
            trial = ensure_unique_slug(slug, used_slugs)
            if trial == slug:
                candidate_slug = trial
                break
        used_slugs.add(candidate_slug)

        final_path = ensure_publish_path(target_dir, candidate_slug)
        source_path = Path(file)
        if source_path != final_path:
            source_path.replace(final_path)

        embedded = embed_metadata(str(final_path), meta)
        meta["embedded"] = embedded
        meta["final_slug"] = final_path.stem

        finalized_path = str(final_path)
        finalized_files.append(finalized_path)
        finalized_metadata[finalized_path] = meta
        finalized_details[finalized_path] = process_info

    return finalized_files, finalized_metadata, finalized_details


def execute_native_attach(
    *,
    site: str,
    request: Dict[str, Any],
    post_context: Dict[str, Any],
    constraints: Dict[str, Any],
) -> Dict[str, Any]:
    failure = validate_attach_request(
        site=site,
        request=request,
        post_context=post_context,
        constraints=constraints,
    )
    if failure:
        return failure

    started = datetime.utcnow()
    selection = resolve_source_images(
        source=request.get("source", "semantic"),
        count=request.get("count"),
        name=request.get("name"),
        query=request.get("query"),
        location_query=request.get("location_query"),
        content_filter=request.get("content_filter"),
        post_context=post_context,
    )
    _icloud_warnings: list[str] = []
    _resolved_files = resolve_icloud_files(selection.get("files", []), _icloud_warnings)
    processed = process_selected_images(_resolved_files)
    processed_images = processed.get("processed_images", [])
    metadata_dict, metadata_warnings = build_native_metadata_map(
        processed_images,
        location_hint=request.get("location_query") or post_context.get("title", ""),
        post_context=post_context,
        mode=request.get("metadata_mode", "auto"),
    )
    approved_files, approved_metadata, approved_details, blocked = quality_gate_native_batch(
        processed_images=processed_images,
        metadata_dict=metadata_dict,
        processed_details=processed.get("processed_details", {}),
        post_context=post_context,
    )
    finalized_files, finalized_metadata, finalized_details = finalize_publish_assets(
        processed_images=approved_files,
        metadata_dict=approved_metadata,
        processed_details=approved_details,
        post_context=post_context,
        work_dir=processed.get("work_dir"),
    )
    published = publish_processed_images(
        site=site,
        post_id=request["post_id"],
        processed_images=finalized_files,
        metadata_dict=finalized_metadata,
    )
    duration_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
    return {
        "command": "attach",
        "site": site,
        "post_id": request.get("post_id"),
        "request": request,
        "post_context": summarize_post_context(post_context),
        "status": "success" if not published.get("failed") else "partial",
        "selected_assets": selection.get("files", []),
        "rejected_assets": blocked,
        "uploaded_media_ids": [item.get("media_id") for item in published.get("uploaded", []) if item.get("media_id")],
        "inserted_blocks": published.get("content_update", {}).get("inserted", 0),
        "uploaded": published.get("uploaded", []),
        "failed_uploads": published.get("failed", []),
        "constraints": constraints,
        "warnings": metadata_warnings,
        "duration_ms": duration_ms,
        "raw": {
            "selection": selection,
            "processed": processed,
            "approved_files": finalized_files,
            "approved_details": finalized_details,
            "published": published,
        },
    }
