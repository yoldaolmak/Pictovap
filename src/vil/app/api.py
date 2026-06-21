"""Thin API surface over the canonical VIL app jobs."""

from __future__ import annotations

from typing import Any, Dict

from src.vil.app.health import run_health_check
from src.vil.app.jobs import run_attach_job
from src.vil.providers.wordpress import fetch_post_context


def review_post(payload: Dict[str, Any]) -> Dict[str, Any]:
    site = payload.get("site", "yoldaolmak")
    post_id = payload.get("post_id")
    try:
        return {
            "command": "review",
            "status": "success",
            "post_context": fetch_post_context(post_id, site=site),
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


def attach_images(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Thin API-style wrapper over the attach job."""
    return run_attach_job(**payload)
