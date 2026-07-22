"""Safe, anonymous summaries for external validation reports."""

from __future__ import annotations

from collections.abc import Mapping
import platform
from typing import Any

from pictovap import __version__


def _length(value: Any) -> int:
    """Return a collection length without exposing its contents."""
    if isinstance(value, (Mapping, list, tuple)):
        return len(value)
    return 0


def summarize_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Create an anonymous, copy-pasteable summary of a visual plan.

    The summary deliberately excludes article text, titles, paths, URLs,
    profile names, candidate metadata, and credentials. It is intended for
    issue reports where a user wants to share useful runtime evidence without
    sharing private content.
    """
    if not isinstance(plan, Mapping):
        raise ValueError("Plan JSON must contain an object")

    brief = plan.get("visual_brief")
    brief = brief if isinstance(brief, Mapping) else {}
    scores = plan.get("fit_scores")
    scores = scores if isinstance(scores, Mapping) else {}
    placement = plan.get("cms_placement")
    placement = placement if isinstance(placement, Mapping) else {}
    runtime = plan.get("runtime")
    runtime = runtime if isinstance(runtime, Mapping) else {}
    provider = runtime.get("provider")
    provider = provider if isinstance(provider, Mapping) else {}

    return {
        "schema_version": 1,
        "pictovap_version": __version__,
        "python_version": platform.python_version(),
        "plan": {
            "article_language": brief.get("article_language"),
            "sections": _length(brief.get("sections")),
            "image_slots": _length(brief.get("image_slots")),
            "candidates_evaluated": int(plan.get("candidates_evaluated", 0) or 0),
            "scored_candidates": sum(_length(value) for value in scores.values()),
            "selected_images": _length(plan.get("provenance_packs")),
            "placements": _length(placement.get("placements")),
        },
        "runtime": {
            "provider_mode": provider.get("mode"),
        },
    }
