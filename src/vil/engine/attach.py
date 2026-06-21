"""Canonical attach orchestration helpers."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Dict, Tuple

from src.main import YOOrchestrator
from src.vil.profiles.yoldaolmak import apply_environment
from src.vil.engine.metadata import build_basic_metadata_map
from src.vil.providers.wordpress import fetch_post_context
from src.vil.engine.processor import process_selected_images
from src.vil.engine.publisher import publish_processed_images
from src.vil.engine.selector import resolve_source_images


def summarize_post_context(post_context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": post_context.get("id"),
        "title": post_context.get("title", ""),
        "slug": post_context.get("slug", ""),
    }


def derive_location_query(post_context: Dict[str, Any]) -> str:
    title = str(post_context.get("title") or "").strip()
    slug = str(post_context.get("slug") or "").replace("-", " ").strip()
    candidate = title or slug
    candidate = re.sub(r"\s+", " ", candidate).strip()
    return candidate


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
    processed = process_selected_images(selection.get("files", []))
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
    processed = process_selected_images(selection.get("files", []))
    processed_images = processed.get("processed_images", [])
    metadata_dict = build_basic_metadata_map(
        processed_images,
        location_hint=request.get("location_query") or post_context.get("title", ""),
        post_context=post_context,
    )
    published = publish_processed_images(
        site=site,
        post_id=request["post_id"],
        processed_images=processed_images,
        metadata_dict=metadata_dict,
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
        "rejected_assets": [],
        "uploaded_media_ids": [item.get("media_id") for item in published.get("uploaded", []) if item.get("media_id")],
        "inserted_blocks": published.get("content_update", {}).get("inserted", 0),
        "uploaded": published.get("uploaded", []),
        "failed_uploads": published.get("failed", []),
        "constraints": constraints,
        "warnings": ["native attach uses basic metadata fallback only"],
        "duration_ms": duration_ms,
        "raw": {
            "selection": selection,
            "processed": processed,
            "published": published,
        },
    }
