"""Job wrappers around the current orchestrator."""

from __future__ import annotations

from typing import Any, Dict

from src.main import YOOrchestrator
from src.vil.profiles.yoldaolmak import apply_environment


def normalize_attach_result(raw: Dict[str, Any]) -> Dict[str, Any]:
    upload_complete = raw.get("steps", {}).get("upload_complete", {})
    uploaded = upload_complete.get("uploaded", [])
    content_update = upload_complete.get("content_update", {})
    return {
        "site": raw.get("site"),
        "post_id": raw.get("post_id"),
        "status": raw.get("status"),
        "selected_assets": raw.get("steps", {}).get("images_loaded", {}).get("files", []),
        "rejected_assets": raw.get("steps", {}).get("quality_gate", {}).get("blocked", []),
        "uploaded_media_ids": [item.get("media_id") for item in uploaded if item.get("media_id")],
        "inserted_blocks": content_update.get("inserted", 0),
        "warnings": raw.get("warning") or raw.get("error"),
        "raw": raw,
    }


def run_attach_job(**kwargs: Any) -> Dict[str, Any]:
    site = kwargs.get("site", "yoldaolmak")
    if site == "yoldaolmak":
        apply_environment()
    orchestrator = YOOrchestrator()
    raw = orchestrator.run_pipeline(**kwargs)
    return normalize_attach_result(raw)
