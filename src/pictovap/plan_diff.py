"""Deterministic, side-effect-free comparison for serialized visual plans."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from pictovap.validation import validate_visual_plan


PLAN_DIFF_SCHEMA_VERSION = "1"

_ARTICLE_FIELDS = (
    "article_title",
    "article_language",
    "topic",
    "detected_location",
    "sections",
    "avoid_list",
    "editorial_notes",
    "frontmatter",
)
_PROFILE_FIELDS = ("id", "brand", "cms_type", "language")
_SLOT_FIELDS = (
    "purpose",
    "preferred_type",
    "target_heading",
    "section_excerpt",
)
_SCORE_FIELDS = (
    "contextual_relevance",
    "section_relevance",
    "technical_quality",
    "duplication_risk",
    "source_trust",
    "license_confidence",
    "cms_suitability",
    "final_score",
    "decision",
    "human_reason",
)
_PROVENANCE_FIELDS = (
    "image_id",
    "provider",
    "source_type",
    "license_status",
    "attribution",
    "content_hash",
    "placement_target",
    "generated_alt_text",
    "generated_caption",
    "processing_actions",
)
_PLACEMENT_FIELDS = (
    "output_path",
    "target_section",
    "placement_strategy",
    "image_role",
    "alt_text",
    "caption",
)
_INTENT_FIELDS = ("role", "target_heading", "purpose", "query_terms", "constraints")
_INTENT_LEDGER_FIELDS = (
    "decision",
    "assignment",
    "reason_codes",
    "human_reason",
    "hard_constraints",
    "soft_constraints",
    "evidence",
)
_DIAGNOSTIC_FIELDS = (
    "slots_requested",
    "slots_filled",
    "coverage_ratio",
    "total_score",
    "adjusted_total_score",
    "diversity_penalty",
    "warnings",
    "unfilled_slots",
)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return value
    return ()


def _field_changes(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    fields: Sequence[str],
) -> list[dict[str, Any]]:
    return [
        {"field": field, "before": before.get(field), "after": after.get(field)}
        for field in fields
        if before.get(field) != after.get(field)
    ]


def _index_records(value: Any, key: str) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for raw in _sequence(value):
        record = _mapping(raw)
        record_key = record.get(key)
        if record_key is None:
            continue
        indexed[str(record_key)] = record
    return indexed


def _record_changes(
    before: Mapping[str, Mapping[str, Any]],
    after: Mapping[str, Mapping[str, Any]],
    fields: Sequence[str],
    *,
    key_name: str,
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for record_key in sorted(set(before) | set(after)):
        if record_key not in before:
            changes.append({
                key_name: record_key,
                "change": "added",
                "before": None,
                "after": dict(after[record_key]),
                "fields": [],
            })
            continue
        if record_key not in after:
            changes.append({
                key_name: record_key,
                "change": "removed",
                "before": dict(before[record_key]),
                "after": None,
                "fields": [],
            })
            continue
        changed_fields = _field_changes(before[record_key], after[record_key], fields)
        if changed_fields:
            changes.append({
                key_name: record_key,
                "change": "modified",
                "before": None,
                "after": None,
                "fields": changed_fields,
            })
    return changes


def _score_index(plan: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for slot_id, raw_scores in _mapping(plan.get("fit_scores")).items():
        for raw_score in _sequence(raw_scores):
            score = _mapping(raw_score)
            candidate_id = score.get("candidate_id")
            if candidate_id is None:
                continue
            key = f"{slot_id}:{candidate_id}"
            indexed[key] = score
    return indexed


def _candidate_ids(plan: Mapping[str, Any]) -> set[str]:
    return {
        str(score.get("candidate_id"))
        for score in _score_index(plan).values()
        if score.get("candidate_id") is not None
    }


def _intent_slots(plan: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    proof = _mapping(plan.get("intent_proof"))
    graph = _mapping(proof.get("graph"))
    return _index_records(graph.get("slots"), "slot_id")


def _intent_ledger(plan: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    proof = _mapping(plan.get("intent_proof"))
    indexed: dict[str, Mapping[str, Any]] = {}
    for raw_entry in _sequence(proof.get("ledger")):
        entry = _mapping(raw_entry)
        slot_id = entry.get("slot_id")
        candidate_id = entry.get("candidate_id")
        if slot_id is None or candidate_id is None:
            continue
        indexed[f"{slot_id}:{candidate_id}"] = entry
    return indexed


def _validation_summary(plan: Mapping[str, Any]) -> dict[str, Any]:
    result = validate_visual_plan(plan)
    return {
        "status": result["status"],
        "error_codes": sorted({str(item.get("code")) for item in result.get("errors", [])}),
        "warning_codes": sorted({str(item.get("code")) for item in result.get("warnings", [])}),
    }


def _article_id(plan: Mapping[str, Any]) -> str:
    brief = _mapping(plan.get("visual_brief"))
    placement = _mapping(plan.get("cms_placement"))
    return str(brief.get("article_id") or placement.get("article_id") or "")


def diff_visual_plans(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare two serialized plans without provider, filesystem, or CMS access.

    The returned schema is deterministic and deliberately compares editorial
    contract fields rather than volatile runtime metadata or source paths.
    """
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        raise TypeError("Both plans must be JSON objects")

    before_brief = _mapping(before.get("visual_brief"))
    after_brief = _mapping(after.get("visual_brief"))
    article_changes = _field_changes(before_brief, after_brief, _ARTICLE_FIELDS)
    profile_changes = _field_changes(
        _mapping(before.get("profile")),
        _mapping(after.get("profile")),
        _PROFILE_FIELDS,
    )
    slot_changes = _record_changes(
        _index_records(before_brief.get("image_slots"), "slot_id"),
        _index_records(after_brief.get("image_slots"), "slot_id"),
        _SLOT_FIELDS,
        key_name="slot_id",
    )

    before_candidates = _candidate_ids(before)
    after_candidates = _candidate_ids(after)
    candidate_pool = {
        "added": sorted(after_candidates - before_candidates),
        "removed": sorted(before_candidates - after_candidates),
    }
    evaluation_changes = _record_changes(
        _score_index(before),
        _score_index(after),
        _SCORE_FIELDS,
        key_name="evaluation",
    )
    selection_changes = _record_changes(
        _index_records(before.get("provenance_packs"), "slot_id"),
        _index_records(after.get("provenance_packs"), "slot_id"),
        _PROVENANCE_FIELDS,
        key_name="slot_id",
    )
    placement_changes = _record_changes(
        _index_records(_mapping(before.get("cms_placement")).get("placements"), "slot_id"),
        _index_records(_mapping(after.get("cms_placement")).get("placements"), "slot_id"),
        _PLACEMENT_FIELDS,
        key_name="slot_id",
    )
    intent_changes = _record_changes(
        _intent_slots(before),
        _intent_slots(after),
        _INTENT_FIELDS,
        key_name="slot_id",
    )
    intent_ledger_changes = _record_changes(
        _intent_ledger(before),
        _intent_ledger(after),
        _INTENT_LEDGER_FIELDS,
        key_name="evaluation",
    )
    diagnostics_changes = _field_changes(
        _mapping(before.get("planning_diagnostics")),
        _mapping(after.get("planning_diagnostics")),
        _DIAGNOSTIC_FIELDS,
    )
    before_id = _article_id(before)
    after_id = _article_id(after)
    article_identity_changed = before_id != after_id

    change_sources: list[str] = []
    if article_identity_changed or article_changes or slot_changes:
        change_sources.append("article")
    if profile_changes:
        change_sources.append("profile")
    if (
        candidate_pool["added"]
        or candidate_pool["removed"]
        or evaluation_changes
        or selection_changes
        or intent_ledger_changes
    ):
        change_sources.append("candidates")
    if intent_changes or intent_ledger_changes or diagnostics_changes:
        change_sources.append("policy")
    if placement_changes:
        change_sources.append("cms_placement")

    summary = {
        "article_identity_changed": int(article_identity_changed),
        "article_fields_changed": len(article_changes),
        "profile_fields_changed": len(profile_changes),
        "slots_changed": len(slot_changes),
        "candidates_added": len(candidate_pool["added"]),
        "candidates_removed": len(candidate_pool["removed"]),
        "evaluations_changed": len(evaluation_changes),
        "selections_changed": len(selection_changes),
        "placements_changed": len(placement_changes),
        "intent_slots_changed": len(intent_changes),
        "intent_ledger_entries_changed": len(intent_ledger_changes),
        "diagnostics_fields_changed": len(diagnostics_changes),
    }
    total_changes = sum(summary.values())

    return {
        "schema_version": PLAN_DIFF_SCHEMA_VERSION,
        "status": "changed" if total_changes else "unchanged",
        "change_sources": change_sources,
        "identity": {
            "before_article_id": before_id,
            "after_article_id": after_id,
            "same_article": before_id == after_id if before_id and after_id else None,
        },
        "input_validation": {
            "before": _validation_summary(before),
            "after": _validation_summary(after),
        },
        "summary": {"total_changes": total_changes, **summary},
        "article_changes": article_changes,
        "profile_changes": profile_changes,
        "slot_changes": slot_changes,
        "candidate_pool": candidate_pool,
        "evaluation_changes": evaluation_changes,
        "selection_changes": selection_changes,
        "placement_changes": placement_changes,
        "intent_changes": intent_changes,
        "intent_ledger_changes": intent_ledger_changes,
        "diagnostics_changes": diagnostics_changes,
    }


def plan_diff_to_json(result: Mapping[str, Any]) -> str:
    """Serialize a plan diff with stable ordering and a trailing newline."""
    return json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _inline(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _render_field_changes(lines: list[str], title: str, changes: Sequence[Mapping[str, Any]]) -> None:
    if not changes:
        return
    lines.extend([f"## {title}", ""])
    for change in changes:
        lines.append(
            f"- `{change.get('field')}`: {_inline(change.get('before'))} → {_inline(change.get('after'))}"
        )
    lines.append("")


def _render_record_changes(
    lines: list[str],
    title: str,
    changes: Sequence[Mapping[str, Any]],
    key_name: str,
) -> None:
    if not changes:
        return
    lines.extend([f"## {title}", ""])
    for change in changes:
        label = str(change.get(key_name, "unknown"))
        change_type = str(change.get("change", "modified"))
        lines.append(f"- `{label}` — **{change_type}**")
        if change_type in {"added", "removed"}:
            details = change.get("after") if change_type == "added" else change.get("before")
            lines.append(f"  - Details: {_inline(details)}")
        for field in _sequence(change.get("fields")):
            field_change = _mapping(field)
            lines.append(
                f"  - `{field_change.get('field')}`: "
                f"{_inline(field_change.get('before'))} → {_inline(field_change.get('after'))}"
            )
    lines.append("")


def render_plan_diff_markdown(result: Mapping[str, Any]) -> str:
    """Render a plan diff for editor and maintainer review."""
    summary = _mapping(result.get("summary"))
    identity = _mapping(result.get("identity"))
    sources = ", ".join(str(item) for item in _sequence(result.get("change_sources"))) or "none"
    lines = [
        "# Pictovap Plan Diff",
        "",
        f"- **Status:** {result.get('status', 'unknown')}",
        "- **Same article:** " + (
            "unknown" if identity.get("same_article") is None
            else "yes" if identity.get("same_article") else "no"
        ),
        f"- **Change sources:** {sources}",
        f"- **Total changes:** {summary.get('total_changes', 0)}",
        "",
        "## Summary",
        "",
        "| Category | Count |",
        "| --- | ---: |",
    ]
    for key in (
        "article_identity_changed",
        "article_fields_changed",
        "profile_fields_changed",
        "slots_changed",
        "candidates_added",
        "candidates_removed",
        "evaluations_changed",
        "selections_changed",
        "placements_changed",
        "intent_slots_changed",
        "intent_ledger_entries_changed",
        "diagnostics_fields_changed",
    ):
        lines.append(f"| {key.replace('_', ' ')} | {summary.get(key, 0)} |")
    lines.append("")

    _render_field_changes(lines, "Article Changes", _sequence(result.get("article_changes")))
    _render_field_changes(lines, "Profile Changes", _sequence(result.get("profile_changes")))
    _render_record_changes(lines, "Slot Changes", _sequence(result.get("slot_changes")), "slot_id")

    candidate_pool = _mapping(result.get("candidate_pool"))
    if candidate_pool.get("added") or candidate_pool.get("removed"):
        lines.extend([
            "## Candidate Pool",
            "",
            f"- **Added:** {_inline(candidate_pool.get('added', []))}",
            f"- **Removed:** {_inline(candidate_pool.get('removed', []))}",
            "",
        ])

    _render_record_changes(
        lines, "Candidate Evaluation Changes", _sequence(result.get("evaluation_changes")), "evaluation"
    )
    _render_record_changes(
        lines, "Selection and Provenance Changes", _sequence(result.get("selection_changes")), "slot_id"
    )
    _render_record_changes(
        lines, "CMS Placement Changes", _sequence(result.get("placement_changes")), "slot_id"
    )
    _render_record_changes(
        lines, "Intent Changes", _sequence(result.get("intent_changes")), "slot_id"
    )
    _render_record_changes(
        lines,
        "Intent Ledger Changes",
        _sequence(result.get("intent_ledger_changes")),
        "evaluation",
    )
    _render_field_changes(
        lines, "Planning Diagnostics Changes", _sequence(result.get("diagnostics_changes"))
    )

    if result.get("status") == "unchanged":
        lines.extend(["No editorial plan changes were detected.", ""])
    return "\n".join(lines)
