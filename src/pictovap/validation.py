"""Side-effect-free validation for serialized visual plans.

The validator is intentionally independent from providers and CMS adapters. It
lets an external integration validate its output in CI without network access,
credentials, or a live CMS.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _object(value: Any, path: str, errors: list[dict[str, str]]) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        errors.append(_issue("object_required", path, "Expected an object."))
        return None
    return value


def _list(value: Any, path: str, errors: list[dict[str, str]]) -> list[Any] | None:
    if not isinstance(value, list):
        errors.append(_issue("list_required", path, "Expected a list."))
        return None
    return value


def _non_empty(value: Any, path: str, errors: list[dict[str, str]]) -> bool:
    if not isinstance(value, str) or not value.strip():
        errors.append(_issue("value_required", path, "Expected a non-empty string."))
        return False
    return True


def validate_visual_plan(plan: Mapping[str, Any], *, strict: bool = False) -> dict[str, Any]:
    """Validate a serialized visual plan without network or filesystem access.

    The default mode checks the stable core contract while allowing additive
    fields from newer Pictovap versions. ``strict=True`` promotes consistency
    warnings (for example, incomplete provenance coverage) to failures. The
    returned object is JSON-serializable and safe to publish in CI logs.
    """
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    checks: dict[str, dict[str, Any]] = {}

    root = _object(plan, "$", errors)
    if root is None:
        return {
            "schema_version": "1",
            "status": "failed",
            "strict": strict,
            "checks": {"root": {"status": "failed"}},
            "errors": errors,
            "warnings": warnings,
            "summary": {"errors": len(errors), "warnings": 0},
        }

    brief = _object(root.get("visual_brief"), "$.visual_brief", errors)
    if brief is not None:
        title_ok = _non_empty(brief.get("article_title"), "$.visual_brief.article_title", errors)
        slots = _list(brief.get("image_slots"), "$.visual_brief.image_slots", errors)
        slot_ids: list[str] = []
        if slots is not None:
            for index, slot in enumerate(slots):
                slot_obj = _object(slot, f"$.visual_brief.image_slots[{index}]", errors)
                if slot_obj is None:
                    continue
                slot_id = slot_obj.get("slot_id")
                if _non_empty(slot_id, f"$.visual_brief.image_slots[{index}].slot_id", errors):
                    if slot_id in slot_ids:
                        errors.append(_issue(
                            "duplicate_slot",
                            f"$.visual_brief.image_slots[{index}].slot_id",
                            "Slot IDs must be unique.",
                        ))
                    else:
                        slot_ids.append(str(slot_id))
        checks["visual_brief"] = {
            "status": "passed" if title_ok and not any(
                item["path"].startswith("$.visual_brief") for item in errors
            ) else "failed",
            "slots": len(slot_ids),
        }
    else:
        slot_ids = []
        checks["visual_brief"] = {"status": "failed"}

    scores = root.get("fit_scores")
    scores_ok = isinstance(scores, Mapping)
    if not scores_ok:
        errors.append(_issue("object_required", "$.fit_scores", "Expected an object keyed by slot ID."))
        scores = {}
    score_count = 0
    for slot_id, raw_scores in scores.items():
        score_list = _list(raw_scores, f"$.fit_scores.{slot_id}", errors)
        if score_list is None:
            continue
        for index, score in enumerate(score_list):
            score_obj = _object(score, f"$.fit_scores.{slot_id}[{index}]", errors)
            if score_obj is None:
                continue
            score_count += 1
            _non_empty(score_obj.get("candidate_id"), f"$.fit_scores.{slot_id}[{index}].candidate_id", errors)
            _non_empty(score_obj.get("slot_id"), f"$.fit_scores.{slot_id}[{index}].slot_id", errors)
            if score_obj.get("decision") not in {"selected", "rejected", "needs_review"}:
                errors.append(_issue(
                    "invalid_decision",
                    f"$.fit_scores.{slot_id}[{index}].decision",
                    "Decision must be selected, rejected, or needs_review.",
                ))
            if not isinstance(score_obj.get("final_score"), (int, float)):
                errors.append(_issue(
                    "number_required",
                    f"$.fit_scores.{slot_id}[{index}].final_score",
                    "Final score must be numeric.",
                ))
    checks["fit_scores"] = {"status": "passed" if scores_ok else "failed", "scores": score_count}

    packs = _list(root.get("provenance_packs"), "$.provenance_packs", errors)
    pack_slots: set[str] = set()
    if packs is not None:
        for index, pack in enumerate(packs):
            pack_obj = _object(pack, f"$.provenance_packs[{index}]", errors)
            if pack_obj is None:
                continue
            _non_empty(pack_obj.get("image_id"), f"$.provenance_packs[{index}].image_id", errors)
            slot_id = pack_obj.get("slot_id")
            if _non_empty(slot_id, f"$.provenance_packs[{index}].slot_id", errors):
                if slot_id in pack_slots:
                    errors.append(_issue(
                        "duplicate_provenance_slot",
                        f"$.provenance_packs[{index}].slot_id",
                        "Only one provenance pack may occupy a slot.",
                    ))
                pack_slots.add(str(slot_id))
            _non_empty(pack_obj.get("provider"), f"$.provenance_packs[{index}].provider", errors)
    else:
        packs = []
    checks["provenance"] = {
        "status": "passed" if isinstance(root.get("provenance_packs"), list) else "failed",
        "packs": len(packs),
    }

    placement = _object(root.get("cms_placement"), "$.cms_placement", errors)
    placement_slots: set[str] = set()
    if placement is not None:
        _non_empty(placement.get("article_id"), "$.cms_placement.article_id", errors)
        placements = _list(placement.get("placements"), "$.cms_placement.placements", errors)
        if placements is None:
            placements = []
        for index, item in enumerate(placements):
            item_obj = _object(item, f"$.cms_placement.placements[{index}]", errors)
            if item_obj is None:
                continue
            slot_id = item_obj.get("slot_id")
            if _non_empty(slot_id, f"$.cms_placement.placements[{index}].slot_id", errors):
                placement_slots.add(str(slot_id))
            _non_empty(item_obj.get("output_path"), f"$.cms_placement.placements[{index}].output_path", errors)
        checks["cms_placement"] = {"status": "passed", "placements": len(placements)}
    else:
        placement_slots = set()
        checks["cms_placement"] = {"status": "failed", "placements": 0}

    diagnostics = root.get("planning_diagnostics")
    if diagnostics is not None and isinstance(diagnostics, Mapping):
        requested = diagnostics.get("slots_requested")
        filled = diagnostics.get("slots_filled")
        ratio = diagnostics.get("coverage_ratio")
        if not isinstance(requested, int) or requested < 0:
            warnings.append(_issue(
                "invalid_diagnostics",
                "$.planning_diagnostics.slots_requested",
                "Expected a non-negative integer.",
            ))
        if not isinstance(filled, int) or filled < 0:
            warnings.append(_issue(
                "invalid_diagnostics",
                "$.planning_diagnostics.slots_filled",
                "Expected a non-negative integer.",
            ))
        if not isinstance(ratio, (int, float)) or not 0 <= ratio <= 1:
            warnings.append(_issue(
                "invalid_diagnostics",
                "$.planning_diagnostics.coverage_ratio",
                "Expected a number between 0 and 1.",
            ))
        checks["diagnostics"] = {"status": "passed"}
    else:
        warnings.append(_issue(
            "diagnostics_missing",
            "$.planning_diagnostics",
            "Planning diagnostics are recommended for auditable integrations.",
        ))
        checks["diagnostics"] = {"status": "warning"}

    missing_provenance = sorted(set(slot_ids) - pack_slots)
    missing_placement = sorted(pack_slots - placement_slots)
    if missing_provenance:
        warnings.append(_issue(
            "incomplete_provenance",
            "$.provenance_packs",
            f"No provenance pack covers {len(missing_provenance)} image slot(s).",
        ))
    if missing_placement:
        warnings.append(_issue(
            "incomplete_placement",
            "$.cms_placement.placements",
            f"No CMS placement covers {len(missing_placement)} provenance slot(s).",
        ))

    if strict and warnings:
        errors.extend({**warning, "code": f"strict_{warning['code']}"} for warning in warnings)
    status = "passed" if not errors else "failed"
    return {
        "schema_version": "1",
        "status": status,
        "strict": strict,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "summary": {"errors": len(errors), "warnings": len(warnings)},
    }
