"""Thin API surface over the canonical VIL app jobs."""

from __future__ import annotations

from typing import Any, Dict

from src.pictova.app.health import run_health_check
from src.pictova.app.jobs import run_attach_job
from src.pictova.engine.attach import build_attach_plan, build_process_result, prepare_attach_request
from src.pictova.providers.wordpress import fetch_post_context


def gallery_query(payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST /gallery — zengin fotoğraf galerisi araması."""
    from src.pictova.engine.gallery import gallery_search, gallery_stats
    query = str(payload.get("query", "")).strip()
    if not query:
        return {"status": "success", "stats": gallery_stats(), "results": []}
    results = gallery_search(
        query,
        count=int(payload.get("count", 10)),
        only_local=bool(payload.get("only_local", True)),
        only_scanned=bool(payload.get("only_scanned", False)),
        city=payload.get("city"),
    )
    return {"status": "success", "query": query, "count": len(results), "results": results}


def search_photos(payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST /search — lokasyon bazlı fotoğraf arama."""
    from src.main import search_semantic_assets
    query = str(payload.get("query", "")).strip()
    if not query:
        return {"status": "failed", "warning": "query gerekli"}
    count = int(payload.get("count", 5))
    include_icloud = bool(payload.get("include_icloud", False))
    content_filter = payload.get("content_filter")
    results = search_semantic_assets(
        location_query=query,
        count=count,
        content_filter=content_filter,
        include_icloud=include_icloud,
    )
    return {"status": "success", "query": query, "count": len(results), "results": results}


def review_post(payload: Dict[str, Any]) -> Dict[str, Any]:
    site = payload.get("site", "yoldaolmak")
    post_id = payload.get("post_id")
    try:
        from src.main import search_semantic_assets
        ctx = fetch_post_context(post_id, site=site)
        slug = str(ctx.get("slug") or "").replace("-", " ")
        title = str(ctx.get("title") or "")
        query = slug or title
        candidates = []
        if query:
            candidates = search_semantic_assets(
                location_query=query,
                count=payload.get("count", 8),
                post_context=ctx,
            )
        return {
            "command": "review",
            "status": "success",
            "post_context": ctx,
            "query": query,
            "photo_candidates": candidates,
            "candidate_count": len(candidates),
        }
    except Exception as exc:
        return {
            "command": "review",
            "status": "failed",
            "post_context": {},
            "warnings": [str(exc)],
        }


def health_status() -> Dict[str, Any]:
    return run_health_check()


def plan_attach(payload: Dict[str, Any]) -> Dict[str, Any]:
    site = payload.get("site", "yoldaolmak")
    request, post_context, constraints = prepare_attach_request(**payload)
    return build_attach_plan(
        site=site,
        request=request,
        post_context=post_context,
        constraints=constraints,
    )


def process_attach(payload: Dict[str, Any]) -> Dict[str, Any]:
    site = payload.get("site", "yoldaolmak")
    request, post_context, constraints = prepare_attach_request(**payload)
    return build_process_result(
        site=site,
        request=request,
        post_context=post_context,
        constraints=constraints,
    )


def attach_images(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Thin API-style wrapper over the attach job."""
    return run_attach_job(**payload)
