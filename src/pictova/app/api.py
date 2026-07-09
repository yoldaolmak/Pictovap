"""Thin API surface over the canonical VIL app jobs."""

from __future__ import annotations

from typing import Any, Dict

from pictova.app.health import run_health_check
from pictova.app.jobs import run_attach_job
from pictova.engine.attach import build_attach_plan, build_process_result, prepare_attach_request
from pictova.providers.wordpress import fetch_post_context, guard_post_media


def gallery_query(payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST /gallery — zengin fotoğraf galerisi araması."""
    from pictova.engine.gallery import gallery_search, gallery_stats
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
    from pictova.main import search_semantic_assets
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
    site = payload.get("site")
    if not site:
        return {"command": "review", "status": "failed", "warning": "site parameter is required"}
    post_id = payload.get("post_id")
    try:
        from pictova.main import search_semantic_assets
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


def guard_post(payload: Dict[str, Any]) -> Dict[str, Any]:
    post_id = payload.get("post_id")
    if not post_id:
        return {"command": "guard", "status": "failed", "warning": "post_id gerekli"}
    return guard_post_media(
        int(post_id),
        site=payload.get("site", "demo"),
        repair=bool(payload.get("repair", False)),
        adopt=bool(payload.get("adopt", False)),
        media_ids=payload.get("media_ids"),
    )


def stats_summary() -> Dict[str, Any]:
    """GET /stats — kısa istatistik özeti."""
    from pictova.engine.gallery import gallery_stats
    from pictova.engine.vision_chain import has_any_vision_source
    stats = gallery_stats()
    scan_pct = int(stats["scanned"] / stats["local"] * 100) if stats["local"] else 0
    return {
        "status": "ok",
        **stats,
        "scan_progress_pct": scan_pct,
        "vision_ready": has_any_vision_source(),
    }


def health_status() -> Dict[str, Any]:
    return run_health_check()


def plan_attach(payload: Dict[str, Any]) -> Dict[str, Any]:
    site = payload.get("site", "demo")
    request, post_context, constraints, brief = prepare_attach_request(**payload)
    return build_attach_plan(
        site=site,
        request=request,
        post_context=post_context,
        constraints=constraints,
    )


def process_attach(payload: Dict[str, Any]) -> Dict[str, Any]:
    site = payload.get("site", "demo")
    request, post_context, constraints, brief = prepare_attach_request(**payload)
    return build_process_result(
        site=site,
        request=request,
        post_context=post_context,
        constraints=constraints,
    )


def attach_images(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Thin API-style wrapper over the attach job."""
    return run_attach_job(**payload)
