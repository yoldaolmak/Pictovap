"""API placeholder for future app surface."""

from __future__ import annotations

from typing import Any, Dict

from src.vil.app.jobs import run_attach_job


def attach_images(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Thin API-style wrapper over the attach job."""
    return run_attach_job(**payload)
