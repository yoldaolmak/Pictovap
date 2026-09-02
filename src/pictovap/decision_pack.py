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
                "placement": placements.get(slot_id),
            },
            "evidence": evidence_by_slot.get(slot_id, []),
        })

    article_id = brief.get("article_id") or placement.get("article_id")
    return {
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
            _list(slot.get("candidates"), f"{path}.candidates", errors)
            proposal = _object(slot.get("proposal"), f"{path}.proposal", errors)
            if proposal is not None:
                candidate_id = proposal.get("candidate_id")
                if candidate_id is not None and not isinstance(candidate_id, str):
                    errors.append(_issue(
                        "decision_pack_candidate_id",
                        f"{path}.proposal.candidate_id",
                        "Candidate ID must be a string or null.",
                    ))
                provenance = proposal.get("provenance")
                if provenance is not None:
                    _object(provenance, f"{path}.proposal.provenance", errors)
                placement = proposal.get("placement")
                if placement is not None:
                    _object(placement, f"{path}.proposal.placement", errors)
            _list(slot.get("evidence"), f"{path}.evidence", errors)
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
