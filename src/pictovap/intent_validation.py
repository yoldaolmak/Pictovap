"""Side-effect-free validation for proof-carrying visual intent records.

The validator checks structure and internal consistency only. It never calls a
provider, reads credentials, or tries to recompute a candidate score.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from pictovap.intent import INTENT_SCHEMA_VERSION


_DECISIONS = {"selected", "rejected", "needs_review"}
_ASSIGNMENTS = {"assigned", "not_assigned"}
_CONSTRAINT_KINDS = {"hard", "soft"}
_CONSTRAINT_STATUSES = {"passed", "failed"}


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _object(value: Any, path: str, errors: list[dict[str, str]]) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        errors.append(_issue("intent_object_required", path, "Expected an object."))
        return None
    return value


def _list(value: Any, path: str, errors: list[dict[str, str]]) -> list[Any] | None:
    if not isinstance(value, list):
        errors.append(_issue("intent_list_required", path, "Expected a list."))
        return None
    return value


def _string(value: Any, code: str, path: str, errors: list[dict[str, str]]) -> bool:
    if not isinstance(value, str) or not value.strip():
        errors.append(_issue(code, path, "Expected a non-empty string."))
        return False
    return True


def validate_intent_proof(
    proof: Any,
    *,
    expected_slot_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Validate an intent proof and return machine-readable error codes.

    ``expected_slot_ids`` lets the enclosing visual plan assert that the proof
    describes exactly the same slots as its VisualBrief. The check is optional
    so standalone proof files remain useful.
    """
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    checks: dict[str, dict[str, Any]] = {}

    root = _object(proof, "$", errors)
    if root is None:
        return {
            "schema_version": "1",
            "status": "failed",
            "checks": {"root": {"status": "failed"}},
            "errors": errors,
            "warnings": warnings,
            "summary": {"errors": len(errors), "warnings": 0},
        }

    if root.get("schema_version") != INTENT_SCHEMA_VERSION:
        errors.append(_issue(
            "intent_schema_version",
            "$.schema_version",
            f"Intent proof schema_version must be {INTENT_SCHEMA_VERSION!r}.",
        ))
    checks["schema"] = {"status": "passed" if not errors else "failed"}

    graph = _object(root.get("graph"), "$.graph", errors)
    graph_slot_ids: list[str] = []
    if graph is not None:
        if graph.get("schema_version") != INTENT_SCHEMA_VERSION:
            errors.append(_issue(
                "intent_graph_schema_version",
                "$.graph.schema_version",
                f"Intent graph schema_version must be {INTENT_SCHEMA_VERSION!r}.",
            ))
        slots = _list(graph.get("slots"), "$.graph.slots", errors)
        if slots is not None:
            for index, raw_slot in enumerate(slots):
                path = f"$.graph.slots[{index}]"
                slot = _object(raw_slot, path, errors)
                if slot is None:
                    continue
                slot_id = slot.get("slot_id")
                if _string(slot_id, "intent_slot_id_required", f"{path}.slot_id", errors):
                    slot_id = str(slot_id)
                    if slot_id in graph_slot_ids:
                        errors.append(_issue(
                            "intent_duplicate_slot",
                            f"{path}.slot_id",
                            "Intent graph slot IDs must be unique.",
                        ))
                    else:
                        graph_slot_ids.append(slot_id)
                constraints = _list(slot.get("constraints"), f"{path}.constraints", errors)
                if constraints is not None:
                    for constraint_index, raw_constraint in enumerate(constraints):
                        constraint_path = f"{path}.constraints[{constraint_index}]"
                        constraint = _object(raw_constraint, constraint_path, errors)
                        if constraint is None:
                            continue
                        _string(
                            constraint.get("code"),
                            "intent_constraint_code_required",
                            f"{constraint_path}.code",
                            errors,
                        )
                        kind = constraint.get("kind")
                        if kind not in _CONSTRAINT_KINDS:
                            errors.append(_issue(
                                "intent_constraint_kind",
                                f"{constraint_path}.kind",
                                "Constraint kind must be hard or soft.",
                            ))
                        _string(
                            constraint.get("requirement"),
                            "intent_constraint_requirement_required",
                            f"{constraint_path}.requirement",
                            errors,
                        )
        checks["graph"] = {"status": "passed" if not any(
            item["path"].startswith("$.graph") for item in errors
        ) else "failed", "slots": len(graph_slot_ids)}
    else:
        checks["graph"] = {"status": "failed", "slots": 0}

    if expected_slot_ids is not None:
        expected = {str(slot_id) for slot_id in expected_slot_ids}
        actual = set(graph_slot_ids)
        if expected != actual:
            errors.append(_issue(
                "intent_slot_set_mismatch",
                "$.graph.slots",
                "Intent graph slots must match the enclosing visual brief.",
            ))

    ledger = _list(root.get("ledger"), "$.ledger", errors)
    ledger_count = 0
    assigned_count = 0
    hard_failure_entries = 0
    assigned_by_slot: dict[str, int] = {}
    if ledger is not None:
        for index, raw_entry in enumerate(ledger):
            path = f"$.ledger[{index}]"
            entry = _object(raw_entry, path, errors)
            if entry is None:
                continue
            ledger_count += 1
            slot_id = entry.get("slot_id")
            slot_valid = _string(slot_id, "intent_ledger_slot_id", f"{path}.slot_id", errors)
            if slot_valid and str(slot_id) not in graph_slot_ids:
                errors.append(_issue(
                    "intent_unknown_ledger_slot",
                    f"{path}.slot_id",
                    "Ledger slot_id must refer to a graph slot.",
                ))
            _string(entry.get("candidate_id"), "intent_ledger_candidate_id", f"{path}.candidate_id", errors)
            if entry.get("decision") not in _DECISIONS:
                errors.append(_issue(
                    "intent_decision_invalid",
                    f"{path}.decision",
                    "Decision must be selected, rejected, or needs_review.",
                ))
            assignment = entry.get("assignment")
            if assignment not in _ASSIGNMENTS:
                errors.append(_issue(
                    "intent_assignment_invalid",
                    f"{path}.assignment",
                    "Assignment must be assigned or not_assigned.",
                ))
            elif assignment == "assigned":
                assigned_count += 1
                if slot_valid:
                    slot_key = str(slot_id)
                    assigned_by_slot[slot_key] = assigned_by_slot.get(slot_key, 0) + 1
                if entry.get("decision") != "selected":
                    errors.append(_issue(
                        "intent_assignment_decision_mismatch",
                        f"{path}.assignment",
                        "An assigned ledger entry must have a selected decision.",
                    ))
            hard_constraints = _list(entry.get("hard_constraints"), f"{path}.hard_constraints", errors)
            soft_constraints = _list(entry.get("soft_constraints"), f"{path}.soft_constraints", errors)
            entry_failed = False
            for constraint_group, constraint_list in (
                ("hard_constraints", hard_constraints),
                ("soft_constraints", soft_constraints),
            ):
                if constraint_list is None:
                    continue
                for constraint_index, raw_constraint in enumerate(constraint_list):
                    constraint_path = f"{path}.{constraint_group}[{constraint_index}]"
                    constraint = _object(raw_constraint, constraint_path, errors)
                    if constraint is None:
                        continue
                    _string(
                        constraint.get("code"),
                        "intent_evaluated_constraint_code",
                        f"{constraint_path}.code",
                        errors,
                    )
                    if constraint.get("status") not in _CONSTRAINT_STATUSES:
                        errors.append(_issue(
                            "intent_constraint_status_invalid",
                            f"{constraint_path}.status",
                            "Evaluated constraint status must be passed or failed.",
                        ))
                    if constraint.get("status") == "failed" and constraint_group == "hard_constraints":
                        entry_failed = True
            if entry_failed:
                hard_failure_entries += 1

    duplicate_assignments = sorted(slot_id for slot_id, count in assigned_by_slot.items() if count > 1)
    if duplicate_assignments:
        errors.append(_issue(
            "intent_multiple_assignments",
            "$.ledger",
            "At most one ledger entry may be assigned to each slot.",
        ))
    checks["ledger"] = {
        "status": "passed" if not any(item["path"].startswith("$.ledger") for item in errors) else "failed",
        "evaluations": ledger_count,
        "assigned": assigned_count,
    }

    summary = _object(root.get("summary"), "$.summary", errors)
    if summary is not None:
        expected_summary = {
            "slots": len(graph_slot_ids),
            "evaluations": ledger_count,
            "selected": assigned_count,
            "hard_constraint_failures": hard_failure_entries,
        }
        for key, expected_value in expected_summary.items():
            value = summary.get(key)
            if type(value) is not int or value != expected_value:
                errors.append(_issue(
                    "intent_summary_mismatch",
                    f"$.summary.{key}",
                    f"Summary field must equal {expected_value} for this proof.",
                ))
        checks["summary"] = {"status": "passed" if not any(
            item["path"].startswith("$.summary") for item in errors
        ) else "failed"}
    else:
        checks["summary"] = {"status": "failed"}

    status = "passed" if not errors else "failed"
    return {
        "schema_version": "1",
        "status": status,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "summary": {"errors": len(errors), "warnings": len(warnings)},
    }


__all__ = ["validate_intent_proof"]
