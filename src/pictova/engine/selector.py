"""Selection helpers exposed from the canonical engine package."""

from __future__ import annotations

from typing import Any, Dict, List

from src.core.processor import get_vil_images
from src.main import load_vil_images_from_index_for_post, search_semantic_assets


def resolve_source_images(
    *,
    source: str,
    count: int | None,
    name: str | None,
    query: str | None,
    location_query: str | None,
    content_filter: str | None,
    post_context: Dict[str, Any],
) -> Dict[str, Any]:
    if source == "semantic":
        files = search_semantic_assets(
            location_query=location_query or "",
            count=count or 5,
            content_filter=content_filter,
            post_context=post_context,
        )
        return {
            "source": "semantic",
            "query": location_query or "",
            "content_filter": content_filter,
            "files": files,
        }

    if source == "vil":
        files = load_vil_images_from_index_for_post(
            count=count,
            name=name,
            post_context=post_context,
        )
        if not files:
            files = get_vil_images(count=count, name=name)
        return {
            "source": "vil",
            "query": name or "",
            "content_filter": None,
            "files": files,
        }

    if source == "unsplash":
        return {
            "source": "unsplash",
            "query": query or "",
            "content_filter": None,
            "files": [],
        }

    raise ValueError(f"Unsupported source: {source}")


__all__ = ["load_vil_images_from_index_for_post", "resolve_source_images", "search_semantic_assets"]
