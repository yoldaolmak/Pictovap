"""Portable, review-ready decision packs built from visual plans.

This module is deliberately side-effect-free. It prepares the plan evidence an
editorial surface needs, but it never contacts providers, reads credentials,
or applies CMS changes.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pictovap.validation import validate_visual_plan


DECISION_PACK_SCHEMA_VERSION = "1"
_KIND = "pictovap.decision-pack"
_REVIEW_STATUSES = {"pending", "reviewed"}
_REVIEW_ACTIONS = {"accept", "replace", "reject"}


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _object(value: Any, path: str, errors: list[dict[str, str]]) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        errors.append(_issue("decision_pack_object_required", path, "Expected an object."))
        return None
    return value


def _list(value: Any, path: str, errors: list[dict[str, str]]) -> list[Any] | None:
    if not isinstance(value, list):
        errors.append(_issue("decision_pack_list_required", path, "Expected a list."))
        return None
    return value


def _string(value: Any, code: str, path: str, errors: list[dict[str, str]]) -> bool:
    if not isinstance(value, str) or not value.strip():
        errors.append(_issue(code, path, "Expected a non-empty string."))
        return False
    return True


def _candidate_ids(
    candidates: list[Any],
    slot_id: str,
    path: str,
    errors: list[dict[str, str]],
) -> tuple[set[str], set[str]]:
    """Return all and selected candidate IDs after validating slot bindings."""
    all_ids: set[str] = set()
    selected_ids: set[str] = set()
    for index, raw_candidate in enumerate(candidates):
        candidate_path = f"{path}[{index}]"
        candidate = _object(raw_candidate, candidate_path, errors)
        if candidate is None:
            continue
        candidate_id = candidate.get("candidate_id")
        if not _string(
            candidate_id,
            "decision_pack_candidate_id",
            f"{candidate_path}.candidate_id",
            errors,
        ):
            continue
        candidate_id = str(candidate_id)
        if candidate_id in all_ids:
            errors.append(_issue(
                "decision_pack_duplicate_candidate",
                f"{candidate_path}.candidate_id",
                "Candidate IDs must be unique within a slot.",
            ))
        all_ids.add(candidate_id)
        candidate_slot_id = candidate.get("slot_id")
        if candidate_slot_id != slot_id:
            errors.append(_issue(
                "decision_pack_candidate_slot_binding",
                f"{candidate_path}.slot_id",
                "Candidate slot_id must match its Decision Pack slot.",
            ))
        if candidate.get("decision") == "selected":
            selected_ids.add(candidate_id)
    return all_ids, selected_ids


def _assigned_candidate_id(
    evidence: list[Any],
    slot_id: str,
    path: str,
    errors: list[dict[str, str]],
) -> str | None:
    """Resolve the final assignment recorded by the intent ledger, if present."""
    assigned_ids: set[str] = set()
    for index, raw_entry in enumerate(evidence):
        if not isinstance(raw_entry, Mapping) or raw_entry.get("assignment") != "assigned":
            continue
        entry_path = f"{path}[{index}]"
        if raw_entry.get("slot_id") != slot_id:
            errors.append(_issue(
                "decision_pack_evidence_slot_binding",
                f"{entry_path}.slot_id",
                "Assigned evidence slot_id must match its Decision Pack slot.",
            ))
        candidate_id = raw_entry.get("candidate_id")
        if _string(
            candidate_id,
            "decision_pack_evidence_candidate_id",
            f"{entry_path}.candidate_id",
            errors,
        ):
            assigned_ids.add(str(candidate_id))
    if len(assigned_ids) > 1:
        errors.append(_issue(
            "decision_pack_ambiguous_assignment",
            path,
            "A slot may contain at most one assigned candidate.",
        ))
        return None
    return next(iter(assigned_ids), None)


def _validate_asset_binding(
    asset: Mapping[str, Any],
    *,
    slot_id: str,
    path: str,
    candidate_ids: set[str],
    expected_candidate_id: str | None,
    errors: list[dict[str, str]],
) -> str | None:
    """Validate one candidate, provenance, and placement as an atomic binding."""
    candidate_id = asset.get("candidate_id")
    if not _string(
        candidate_id,
        "decision_pack_candidate_id",
        f"{path}.candidate_id",
        errors,
    ):
        candidate_id = None
    else:
        candidate_id = str(candidate_id)
        if candidate_id not in candidate_ids:
            errors.append(_issue(
                "decision_pack_unknown_candidate",
                f"{path}.candidate_id",
                "Asset candidate_id must refer to a scored candidate in the same slot.",
            ))
        if expected_candidate_id is not None and candidate_id != expected_candidate_id:
            errors.append(_issue(
                "decision_pack_selected_candidate_binding",
                f"{path}.candidate_id",
                "Proposal candidate_id must match the candidate assigned by the visual plan.",
            ))

    generated_filename = None
    provenance = _object(asset.get("provenance"), f"{path}.provenance", errors)
    if provenance is not None:
        image_id = provenance.get("image_id")
        _string(
            image_id,
            "decision_pack_provenance_image_id",
            f"{path}.provenance.image_id",
            errors,
        )
        _string(
            provenance.get("provider"),
            "decision_pack_provenance_provider",
            f"{path}.provenance.provider",
            errors,
        )
        generated_filename = provenance.get("generated_filename")
        _string(
            generated_filename,
            "decision_pack_provenance_filename",
            f"{path}.provenance.generated_filename",
            errors,
        )
        if candidate_id is not None and image_id != candidate_id:
            errors.append(_issue(
                "decision_pack_provenance_candidate_binding",
                f"{path}.provenance.image_id",
                "Provenance image_id must match the bound candidate_id.",
            ))
        if provenance.get("slot_id") != slot_id:
            errors.append(_issue(
                "decision_pack_provenance_slot_binding",
                f"{path}.provenance.slot_id",
                "Provenance slot_id must match the Decision Pack slot.",
            ))

    placement = _object(asset.get("placement"), f"{path}.placement", errors)
    if placement is not None:
        output_path = placement.get("output_path")
        _string(
            output_path,
            "decision_pack_placement_output_path",
            f"{path}.placement.output_path",
            errors,
        )
        if (
            isinstance(output_path, str)
            and isinstance(generated_filename, str)
            and output_path.replace("\\", "/").rsplit("/", 1)[-1]
            != generated_filename.replace("\\", "/").rsplit("/", 1)[-1]
        ):
            errors.append(_issue(
                "decision_pack_placement_asset_binding",
                f"{path}.placement.output_path",
                "Placement output_path must resolve to the provenance generated_filename.",
            ))
        if placement.get("slot_id") != slot_id:
            errors.append(_issue(
                "decision_pack_placement_slot_binding",
                f"{path}.placement.slot_id",
                "Placement slot_id must match the Decision Pack slot.",
            ))
        if candidate_id is not None and placement.get("candidate_id") != candidate_id:
            errors.append(_issue(
                "decision_pack_placement_candidate_binding",
                f"{path}.placement.candidate_id",
                "Placement candidate_id must match the bound candidate_id.",
            ))
    return candidate_id


def _asset_is_empty(asset: Mapping[str, Any]) -> bool:
    return all(asset.get(field) is None for field in ("candidate_id", "provenance", "placement"))


def _asset_is_complete(asset: Any) -> bool:
    return (
        isinstance(asset, Mapping)
        and isinstance(asset.get("candidate_id"), str)
        and bool(asset.get("candidate_id", "").strip())
        and isinstance(asset.get("provenance"), Mapping)
        and isinstance(asset.get("placement"), Mapping)
    )


def build_decision_pack(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Build a portable review package from one validated visual plan.

    The source plan remains the computational record. A Decision Pack groups
    its candidate, provenance, placement, and intent evidence by slot, then
    adds empty review and application state for a downstream editorial surface.
    """
    validation = validate_visual_plan(plan)
    if validation["status"] != "passed":
        raise ValueError("Visual plan must pass validation before building a Decision Pack.")

    brief = plan["visual_brief"]
    packs = {
        str(pack["slot_id"]): dict(pack)
        for pack in plan["provenance_packs"]
        if isinstance(pack, Mapping) and isinstance(pack.get("slot_id"), str)
    }
    placement = plan["cms_placement"]
    placements = {
        str(item["slot_id"]): dict(item)
        for item in placement["placements"]
        if isinstance(item, Mapping) and isinstance(item.get("slot_id"), str)
    }
    proof = plan.get("intent_proof")
    raw_ledger = proof.get("ledger", []) if isinstance(proof, Mapping) else []
    evidence_by_slot: dict[str, list[dict[str, Any]]] = {}
    for entry in raw_ledger:
        if isinstance(entry, Mapping) and isinstance(entry.get("slot_id"), str):
            evidence_by_slot.setdefault(str(entry["slot_id"]), []).append(dict(entry))

    slots: list[dict[str, Any]] = []
    for raw_slot in brief["image_slots"]:
        if not isinstance(raw_slot, Mapping):
            continue
        slot = dict(raw_slot)
        slot_id = str(slot["slot_id"])
        provenance = packs.get(slot_id)
        slot_placement = placements.get(slot_id)
        if slot_placement is not None and provenance is not None:
            slot_placement["candidate_id"] = provenance.get("image_id")
        slots.append({
            "slot_id": slot_id,
            "purpose": str(slot.get("purpose", "")),
            "target_heading": str(slot.get("target_heading", "")),
            "candidates": [
                dict(score) for score in plan["fit_scores"].get(slot_id, [])
                if isinstance(score, Mapping)
            ],
            "proposal": {
                "candidate_id": provenance.get("image_id") if provenance else None,
                "provenance": provenance,
                "placement": slot_placement,
            },
            "evidence": evidence_by_slot.get(slot_id, []),
        })

    article_id = brief.get("article_id") or placement.get("article_id")
    decision_pack = {
        "schema_version": DECISION_PACK_SCHEMA_VERSION,
        "kind": _KIND,
        "article": {
            "id": article_id,
            "title": brief.get("article_title"),
            "language": brief.get("article_language"),
        },
        "slots": slots,
        "review": {"status": "pending", "decisions": []},
        "application": {"status": "not_applied", "receipts": []},
    }
    decision_pack_validation = validate_decision_pack(decision_pack)
    if decision_pack_validation["status"] != "passed":
        codes = ", ".join(error["code"] for error in decision_pack_validation["errors"])
        raise ValueError(
            "Visual plan cannot produce a semantically bound Decision Pack: " + codes
        )
    return decision_pack


def validate_decision_pack(pack: Any) -> dict[str, Any]:
    """Validate a Decision Pack without contacting a provider or CMS."""
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    checks: dict[str, dict[str, Any]] = {}

    root = _object(pack, "$", errors)
    if root is None:
        return {
            "schema_version": DECISION_PACK_SCHEMA_VERSION,
            "status": "failed",
            "checks": {"root": {"status": "failed"}},
            "errors": errors,
            "warnings": warnings,
            "summary": {"errors": len(errors), "warnings": 0},
        }

    if root.get("schema_version") != DECISION_PACK_SCHEMA_VERSION:
        errors.append(_issue(
            "decision_pack_schema_version",
            "$.schema_version",
            f"Decision Pack schema_version must be {DECISION_PACK_SCHEMA_VERSION!r}.",
        ))
    if root.get("kind") != _KIND:
        errors.append(_issue("decision_pack_kind", "$.kind", f"Decision Pack kind must be {_KIND!r}."))
    checks["schema"] = {"status": "passed" if not errors else "failed"}

    article = _object(root.get("article"), "$.article", errors)
    if article is not None:
        _string(article.get("id"), "decision_pack_article_id", "$.article.id", errors)
        _string(article.get("title"), "decision_pack_article_title", "$.article.title", errors)
    checks["article"] = {"status": "passed" if article is not None and not any(
        item["path"].startswith("$.article") for item in errors
    ) else "failed"}

    raw_slots = _list(root.get("slots"), "$.slots", errors)
    slot_ids: set[str] = set()
    slots_by_id: dict[str, Mapping[str, Any]] = {}
    if raw_slots is not None:
        for index, raw_slot in enumerate(raw_slots):
            path = f"$.slots[{index}]"
            slot = _object(raw_slot, path, errors)
            if slot is None:
                continue
            slot_id = slot.get("slot_id")
            if _string(slot_id, "decision_pack_slot_id", f"{path}.slot_id", errors):
                slot_id = str(slot_id)
                if slot_id in slot_ids:
                    errors.append(_issue(
                        "decision_pack_duplicate_slot",
                        f"{path}.slot_id",
                        "Decision Pack slot IDs must be unique.",
                    ))
                slot_ids.add(slot_id)
                slots_by_id[slot_id] = slot
            candidates = _list(slot.get("candidates"), f"{path}.candidates", errors)
            evidence = _list(slot.get("evidence"), f"{path}.evidence", errors)
            candidate_ids: set[str] = set()
            selected_ids: set[str] = set()
            assigned_candidate_id = None
            if candidates is not None and isinstance(slot_id, str):
                candidate_ids, selected_ids = _candidate_ids(
                    candidates, slot_id, f"{path}.candidates", errors
                )
            if evidence is not None and isinstance(slot_id, str):
                assigned_candidate_id = _assigned_candidate_id(
                    evidence, slot_id, f"{path}.evidence", errors
                )
            proposal = _object(slot.get("proposal"), f"{path}.proposal", errors)
            if proposal is not None and isinstance(slot_id, str):
                if _asset_is_empty(proposal):
                    if assigned_candidate_id is not None:
                        errors.append(_issue(
                            "decision_pack_assigned_proposal_missing",
                            f"{path}.proposal",
                            "An assigned candidate requires complete proposal evidence.",
                        ))
                else:
                    expected_candidate_id = assigned_candidate_id
                    if expected_candidate_id is None:
                        if len(selected_ids) == 1:
                            expected_candidate_id = next(iter(selected_ids))
                        elif len(selected_ids) > 1:
                            errors.append(_issue(
                                "decision_pack_ambiguous_selected_candidate",
                                f"{path}.candidates",
                                "Multiple selected candidates require one assigned intent-ledger entry.",
                            ))
                        else:
                            errors.append(_issue(
                                "decision_pack_selected_candidate_missing",
                                f"{path}.candidates",
                                "A proposal requires one selected candidate or assigned intent-ledger entry.",
                            ))
                    elif expected_candidate_id not in candidate_ids:
                        errors.append(_issue(
                            "decision_pack_assignment_candidate_binding",
                            f"{path}.evidence",
                            "Assigned evidence must refer to a scored candidate in the same slot.",
                        ))
                    _validate_asset_binding(
                        proposal,
                        slot_id=slot_id,
                        path=f"{path}.proposal",
                        candidate_ids=candidate_ids,
                        expected_candidate_id=expected_candidate_id,
                        errors=errors,
                    )
    checks["slots"] = {"status": "passed" if raw_slots is not None and not any(
        item["path"].startswith("$.slots") for item in errors
    ) else "failed", "slots": len(slot_ids)}

    review = _object(root.get("review"), "$.review", errors)
    decision_slots: set[str] = set()
    if review is not None:
        status = review.get("status")
        if status not in _REVIEW_STATUSES:
            errors.append(_issue(
                "decision_pack_review_status",
                "$.review.status",
                "Review status must be pending or reviewed.",
            ))
        decisions = _list(review.get("decisions"), "$.review.decisions", errors)
        if decisions is not None:
            for index, raw_decision in enumerate(decisions):
                path = f"$.review.decisions[{index}]"
                decision = _object(raw_decision, path, errors)
                if decision is None:
                    continue
                slot_id = decision.get("slot_id")
                if _string(slot_id, "decision_pack_review_slot", f"{path}.slot_id", errors):
                    slot_id = str(slot_id)
                    if slot_id not in slot_ids:
                        errors.append(_issue(
                            "decision_pack_unknown_review_slot",
                            f"{path}.slot_id",
                            "Review decision must refer to a Decision Pack slot.",
                        ))
                    if slot_id in decision_slots:
                        errors.append(_issue(
                            "decision_pack_duplicate_review_slot",
                            f"{path}.slot_id",
                            "Only one review decision may exist for a slot.",
                        ))
                    decision_slots.add(slot_id)
                if decision.get("action") not in _REVIEW_ACTIONS:
                    errors.append(_issue(
                        "decision_pack_review_action",
                        f"{path}.action",
                        "Review action must be accept, replace, or reject.",
                    ))
                action = decision.get("action")
                replacement = decision.get("replacement")
                decision_slot = slots_by_id.get(str(slot_id)) if isinstance(slot_id, str) else None
                if action == "accept" and (
                    decision_slot is None or not _asset_is_complete(decision_slot.get("proposal"))
                ):
                    errors.append(_issue(
                        "decision_pack_accept_requires_proposal",
                        f"{path}.action",
                        "An accept decision requires complete bound proposal evidence.",
                    ))
                if action == "replace":
                    replacement_obj = None
                    if not isinstance(replacement, Mapping):
                        errors.append(_issue(
                            "decision_pack_replacement_required",
                            f"{path}.replacement",
                            "A replace decision requires candidate, provenance, and placement evidence.",
                        ))
                    else:
                        replacement_obj = replacement
                    if replacement_obj is not None and decision_slot is not None:
                        raw_candidates = decision_slot.get("candidates")
                        candidate_ids = set()
                        if isinstance(raw_candidates, list):
                            candidate_ids = {
                                str(item.get("candidate_id"))
                                for item in raw_candidates
                                if isinstance(item, Mapping)
                                and isinstance(item.get("candidate_id"), str)
                                and item.get("candidate_id", "").strip()
                            }
                        replacement_id = _validate_asset_binding(
                            replacement_obj,
                            slot_id=str(slot_id),
                            path=f"{path}.replacement",
                            candidate_ids=candidate_ids,
                            expected_candidate_id=None,
                            errors=errors,
                        )
                        proposal = decision_slot.get("proposal")
                        if (
                            replacement_id is not None
                            and isinstance(proposal, Mapping)
                            and replacement_id == proposal.get("candidate_id")
                        ):
                            errors.append(_issue(
                                "decision_pack_replacement_must_differ",
                                f"{path}.replacement.candidate_id",
                                "Replacement candidate_id must differ from the proposal.",
                            ))
                elif replacement is not None:
                    errors.append(_issue(
                        "decision_pack_unexpected_replacement",
                        f"{path}.replacement",
                        "Only a replace decision may contain replacement evidence.",
                    ))
                _string(decision.get("actor"), "decision_pack_review_actor", f"{path}.actor", errors)
                _string(decision.get("decided_at"), "decision_pack_review_time", f"{path}.decided_at", errors)
        if status == "reviewed" and decision_slots != slot_ids:
            errors.append(_issue(
                "decision_pack_incomplete_review",
                "$.review.decisions",
                "A reviewed Decision Pack must contain one decision for every slot.",
            ))
    checks["review"] = {"status": "passed" if review is not None and not any(
        item["path"].startswith("$.review") for item in errors
    ) else "failed", "decisions": len(decision_slots)}

    application = _object(root.get("application"), "$.application", errors)
    if application is not None:
        if application.get("status") != "not_applied":
            errors.append(_issue(
                "decision_pack_application_status",
                "$.application.status",
                "Decision Pack v1 only represents the not_applied state.",
            ))
        receipts = _list(application.get("receipts"), "$.application.receipts", errors)
        if receipts is not None and receipts:
            errors.append(_issue(
                "decision_pack_application_receipts",
                "$.application.receipts",
                "Decision Pack v1 must not contain application receipts.",
            ))
    checks["application"] = {"status": "passed" if application is not None and not any(
        item["path"].startswith("$.application") for item in errors
    ) else "failed"}

    return {
        "schema_version": DECISION_PACK_SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "summary": {"errors": len(errors), "warnings": len(warnings)},
    }


__all__ = ["DECISION_PACK_SCHEMA_VERSION", "build_decision_pack", "validate_decision_pack"]
