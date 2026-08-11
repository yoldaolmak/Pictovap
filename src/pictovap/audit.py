"""Auditable summaries for serialized visual plans.

The audit boundary is deliberately read-only. It combines the public plan
validator with editorial metrics useful to a human reviewer and to a CI gate,
without contacting providers, reading credentials, or inspecting the
filesystem.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Any

from pictovap.validation import validate_visual_plan


def _status(status: str, detail: str, **extra: Any) -> dict[str, Any]:
    return {"status": status, "detail": detail, **extra}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _int_or(value: Any, fallback: int) -> int:
    return value if type(value) is int else fallback


def _warning_or_failed(strict: bool, detail: str, **extra: Any) -> dict[str, Any]:
    return _status("failed" if strict else "warning", detail, **extra)


def audit_visual_plan(plan: Mapping[str, Any], *, strict: bool = False) -> dict[str, Any]:
    """Return a JSON-safe editorial and integration audit for one visual plan.

    ``strict=False`` keeps incomplete editorial information visible as warnings
    so a reviewer can still inspect a draft. ``strict=True`` turns every
    recommendation into a CI failure while preserving the same metrics.
    """
    validation = validate_visual_plan(plan, strict=strict)
    root = _as_mapping(plan)
    brief = _as_mapping(root.get("visual_brief"))
    slots = _as_list(brief.get("image_slots"))
    slot_ids = [
        str(slot.get("slot_id"))
        for slot in slots
        if isinstance(slot, Mapping) and _non_empty(slot.get("slot_id"))
    ]

    raw_scores = root.get("fit_scores")
    scores = raw_scores if isinstance(raw_scores, Mapping) else {}
    score_rows = [
        score
        for slot_scores in scores.values()
        for score in _as_list(slot_scores)
        if isinstance(score, Mapping)
    ]
    selected = [score for score in score_rows if score.get("decision") == "selected"]
    needs_review = [score for score in score_rows if score.get("decision") == "needs_review"]
    rejected = [score for score in score_rows if score.get("decision") == "rejected"]
    selected_slots = {str(score.get("slot_id")) for score in selected if _non_empty(score.get("slot_id"))}
    selected_ids = [str(score.get("candidate_id")) for score in selected if _non_empty(score.get("candidate_id"))]
    duplicate_selected = sorted(
        candidate_id for candidate_id, count in Counter(selected_ids).items() if count > 1
    )

    packs = _as_list(root.get("provenance_packs"))
    pack_rows = [pack for pack in packs if isinstance(pack, Mapping)]
    pack_slots = {str(pack.get("slot_id")) for pack in pack_rows if _non_empty(pack.get("slot_id"))}
    license_statuses = Counter(
        str(pack.get("license_status") or pack.get("license") or "missing").lower()
        for pack in pack_rows
    )
    missing_license = sum(
        count for status, count in license_statuses.items() if status in {"", "missing", "unknown"}
    )

    placement = _as_mapping(root.get("cms_placement"))
    placements = [item for item in _as_list(placement.get("placements")) if isinstance(item, Mapping)]
    placement_slots = {str(item.get("slot_id")) for item in placements if _non_empty(item.get("slot_id"))}
    accessible_placements = sum(1 for item in placements if _non_empty(item.get("alt_text")))
    diagnostics = _as_mapping(root.get("planning_diagnostics"))
    requested = _int_or(diagnostics.get("slots_requested"), len(slot_ids))
    filled = _int_or(diagnostics.get("slots_filled"), len(placements))
    coverage_ratio = (filled / requested) if requested else 1.0

    missing_provenance = sorted(selected_slots - pack_slots)
    metrics = {
        "slots_requested": len(slot_ids),
        "slots_filled": len(placement_slots & set(slot_ids)),
        "coverage_ratio": round(coverage_ratio, 4),
        "candidates_evaluated": len(score_rows),
        "selected_candidates": len(selected),
        "needs_review": len(needs_review),
        "rejected_candidates": len(rejected),
        "provenance_records": len(pack_rows),
        "placements": len(placements),
        "accessible_placements": accessible_placements,
        "license_statuses": dict(sorted(license_statuses.items())),
        "duplicate_selected_candidate_ids": duplicate_selected,
    }

    checks: dict[str, dict[str, Any]] = {
        "plan_validation": _status(
            "passed" if validation["status"] == "passed" else "failed",
            "The serialized plan satisfies the public structural contract."
            if validation["status"] == "passed" else "The serialized plan has contract errors.",
            errors=validation["summary"]["errors"],
            warnings=validation["summary"]["warnings"],
        ),
        "coverage": _status(
            "passed" if not requested or filled >= requested else ("failed" if strict else "warning"),
            "All requested slots have placement instructions."
            if not requested or filled >= requested else
            f"{requested - filled} requested slot(s) have no placement instruction.",
            requested=requested,
            filled=filled,
        ),
        "provenance": _status(
            "passed"
            if not missing_provenance and (not pack_rows or not missing_license)
            else ("failed" if strict else "warning"),
            "Selected images have provenance records with known license status."
            if not missing_provenance and not missing_license else
            "Selected images need provenance records or a non-unknown license status.",
            missing_slots=missing_provenance,
            missing_license_records=missing_license,
        ),
        "accessibility": _status(
            "passed" if len(placements) == accessible_placements else ("failed" if strict else "warning"),
            "Every placement includes non-empty alt text."
            if len(placements) == accessible_placements else
            f"{len(placements) - accessible_placements} placement(s) have no alt text.",
            placements=len(placements),
            with_alt_text=accessible_placements,
        ),
        "review_queue": _warning_or_failed(
            strict,
            f"{len(needs_review)} candidate(s) still need human review.",
            count=len(needs_review),
        ) if needs_review else _status("passed", "No candidate is waiting for human review.", count=0),
        "duplicate_selection": _warning_or_failed(
            strict,
            "The same candidate is selected for more than one slot.",
            candidate_ids=duplicate_selected,
        ) if duplicate_selected else _status("passed", "Selected candidate IDs are unique.", candidate_ids=[]),
    }

    failed_checks = sum(check["status"] == "failed" for check in checks.values())
    warning_checks = sum(check["status"] == "warning" for check in checks.values())
    status = "failed" if failed_checks else ("warning" if warning_checks else "passed")
    return {
        "schema_version": "1",
        "status": status,
        "strict": strict,
        "metrics": metrics,
        "checks": checks,
        "validation": validation,
        "summary": {"failed": failed_checks, "warnings": warning_checks},
    }


def render_audit_markdown(audit: Mapping[str, Any]) -> str:
    """Render an audit result as a concise editor-facing Markdown report."""
    metrics = _as_mapping(audit.get("metrics"))
    checks = _as_mapping(audit.get("checks"))
    lines = [
        "# Pictovap Plan Audit",
        "",
        f"**Status:** `{audit.get('status', 'unknown')}`  ",
        f"**Strict mode:** `{bool(audit.get('strict'))}`",
        "",
        "## Editorial summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    labels = {
        "slots_requested": "Slots requested",
        "slots_filled": "Slots filled",
        "coverage_ratio": "Coverage ratio",
        "candidates_evaluated": "Candidates evaluated",
        "selected_candidates": "Selected candidates",
        "needs_review": "Needs review",
        "rejected_candidates": "Rejected candidates",
        "provenance_records": "Provenance records",
        "placements": "CMS placements",
        "accessible_placements": "Placements with alt text",
    }
    for key, label in labels.items():
        lines.append(f"| {label} | {metrics.get(key, 0)} |")
    lines.extend(["", "## Checks", "", "| Check | Status | Detail |", "| --- | --- | --- |"])
    for name, check in checks.items():
        detail = str(check.get("detail", "")).replace("|", "\\|")
        lines.append(f"| {name.replace('_', ' ').title()} | `{check.get('status', 'unknown')}` | {detail} |")
    duplicates = _as_list(metrics.get("duplicate_selected_candidate_ids"))
    if duplicates:
        lines.extend(["", "**Duplicate selected candidates:** " + ", ".join(map(str, duplicates))])
    lines.append("")
    return "\n".join(lines)


__all__ = ["audit_visual_plan", "render_audit_markdown"]
