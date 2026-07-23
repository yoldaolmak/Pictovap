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


def render_feedback_markdown(summary: Mapping[str, Any]) -> str:
    """Render an anonymous validation summary as a GitHub issue body."""
    plan = summary.get("plan")
    plan = plan if isinstance(plan, Mapping) else {}
    runtime = summary.get("runtime")
    runtime = runtime if isinstance(runtime, Mapping) else {}

    def value(key: str) -> Any:
        resolved = plan.get(key)
        return "unknown" if resolved is None else resolved

    provider_mode = runtime.get("provider_mode")
    provider_mode = "unknown" if provider_mode is None else provider_mode

    return "\n".join([
        "## Pictovap External Validation",
        "",
        "### Environment",
        "",
        f"- Pictovap version: `{summary.get('pictovap_version', 'unknown')}`",
        f"- Python version: `{summary.get('python_version', 'unknown')}`",
        "- OS: <!-- macOS / Ubuntu / Windows / other -->",
        "",
        "### Anonymous Plan Summary",
        "",
        f"- Article language: `{value('article_language')}`",
        f"- Sections: `{value('sections')}`",
        f"- Image slots: `{value('image_slots')}`",
        f"- Candidates evaluated: `{value('candidates_evaluated')}`",
        f"- Scored candidates: `{value('scored_candidates')}`",
        f"- Selected images: `{value('selected_images')}`",
        f"- Placements: `{value('placements')}`",
        f"- Provider mode: `{provider_mode}`",
        "",
        "### Result",
        "",
        "- [ ] The command completed successfully.",
        "- [ ] The visual slots matched the article structure.",
        "- [ ] The report was clear enough for editorial review.",
        "- [ ] I found a bug or confusing output.",
        "",
        "### Notes",
        "",
        "<!-- Do not paste private article text, private paths, image URLs, or credentials. -->",
        "",
    ])


__all__ = ["render_feedback_markdown", "summarize_plan"]
