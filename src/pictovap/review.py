"""Side-effect-free comparison of proposed and editor-reviewed Decision Packs.

A review is an editorial decision, not a CMS operation or a license grant.
This module only inspects already serialized evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from pictovap.decision_pack import validate_decision_pack


def _validated(pack: Mapping[str, Any], label: str) -> None:
    result = validate_decision_pack(pack)
    if result["status"] != "passed":
        codes = [item["code"] for item in result["errors"]]
        raise ValueError(f"{label} Decision Pack is invalid: {codes}")


def _license_status(asset: Any) -> str:
    if not isinstance(asset, Mapping):
        return "unknown"
    provenance = asset.get("provenance")
    if not isinstance(provenance, Mapping):
        return "unknown"
    status = provenance.get("license_status")
    return status if isinstance(status, str) and status.strip() else "unknown"


def preview_decision_pack(
    proposed: Mapping[str, Any],
    reviewed: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare only review decisions against the *same* immutable proposal.

    Both packs must be valid, and no candidate, article, proposal, application
    state or other source evidence may differ. This is not a visual-plan diff.
    """
    _validated(proposed, "Proposed")
    _validated(reviewed, "Reviewed")
    original = deepcopy(dict(proposed))
    submitted = deepcopy(dict(reviewed))
    submitted["review"] = deepcopy(original["review"])
    if submitted != original:
        raise ValueError("Reviewed pack changed proposal evidence or application state")

    decisions = {
        decision["slot_id"]: decision
        for decision in reviewed["review"]["decisions"]
    }
    rows = []
    rights_unknown = 0
    selected = 0
    for slot in proposed["slots"]:
        slot_id = slot["slot_id"]
        proposal = slot["proposal"]
        decision = decisions.get(slot_id)
        action = decision["action"] if decision else "pending"
        original_candidate = proposal.get("candidate_id")
        active_asset: Any = None
        if action == "accept":
            active_asset = proposal
        elif action == "replace":
            active_asset = decision["replacement"]
        if active_asset is not None:
            selected += 1
        status = _license_status(active_asset) if active_asset is not None else "not_selected"
        if active_asset is not None and status.lower() in {"unknown", "none", "unverified"}:
            rights_unknown += 1
        rows.append({
            "slot_id": slot_id,
            "purpose": slot.get("purpose") or "",
            "action": action,
            "proposed_candidate": original_candidate,
            "reviewed_candidate": (
                active_asset.get("candidate_id")
                if isinstance(active_asset, Mapping)
                else None
            ),
            "license_evidence": status,
        })

    return {
        "kind": "pictovap.review-preview",
        "article": deepcopy(proposed["article"]),
        "review_status": reviewed["review"]["status"],
        "application_status": reviewed["application"]["status"],
        "summary": {
            "slots": len(rows),
            "decisions": len(decisions),
            "images_kept": selected,
            "rights_unresolved": rights_unknown,
        },
        "slots": rows,
    }


def _cell(value: Any) -> str:
    """Escape untrusted editorial text in generated Markdown table cells."""
    if value is None:
        return "—"
    return str(value).replace("|", r"\|").replace("\n", " ").replace("\r", " ")


def render_review_preview(preview: Mapping[str, Any]) -> str:
    """Render a human-readable, read-only editorial comparison."""
    article = preview["article"]
    summary = preview["summary"]
    lines = [
        "# Pictovap — Editor Review Preview",
        "",
        f"**Article:** {_cell(article.get('title'))}",
        f"**Review:** {_cell(preview['review_status'])}",
        f"**Application:** {_cell(preview['application_status'])} (no CMS write)",
        "",
        "| Slot | Decision | Proposed | Reviewed | License evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in preview["slots"]:
        lines.append(
            f"| {_cell(row['slot_id'])} | {_cell(row['action'])} "
            f"| {_cell(row['proposed_candidate'])} "
            f"| {_cell(row['reviewed_candidate'])} "
            f"| {_cell(row['license_evidence'])} |"
        )
    lines.extend([
        "",
        f"**Decisions:** {summary['decisions']}/{summary['slots']}  ",
        f"**Images kept:** {summary['images_kept']}  ",
        f"**Unknown rights evidence:** {summary['rights_unresolved']}",
        "",
        "Editorial review does not grant image rights, authorize a CMS action, "
        "or independently verify publication.",
        "",
    ])
    return "\n".join(lines)


__all__ = ["preview_decision_pack", "render_review_preview"]
