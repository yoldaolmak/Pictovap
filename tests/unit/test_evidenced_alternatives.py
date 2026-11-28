"""Editor alternatives come from actual plan candidates, never invented UI metadata."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from actovisio_framework.core.profile import PublisherProfile
from actovisio_framework.data.demo_candidates import MOCK_CANDIDATES
from actovisio_framework.decision_pack import (
    build_decision_pack,
    transition_decision_pack_review,
    validate_decision_pack,
)
from actovisio_framework.engine.planner import build_visual_plan
from actovisio_framework.review import preview_decision_pack
from actovisio_framework.validation import validate_visual_plan


ROOT = Path(__file__).resolve().parents[2]


def _real_planning_slice():
    profile = PublisherProfile(profile_id="editor-demo", brand_name="Editor demo")
    plan = build_visual_plan(
        ROOT / "examples/articles/travel-guide.md",
        profile,
        use_real_sources=False,
        fallback_candidates=MOCK_CANDIDATES,
        fallback_mode="demo",
    )
    validation = validate_visual_plan(plan)
    assert validation["status"] == "passed", validation["errors"]
    return plan


def _complete_review(pack, replacing_slot=None, replacement=None):
    decisions = []
    for slot in pack["slots"]:
        action = (
            "replace" if slot["slot_id"] == replacing_slot
            else "accept" if slot["proposal"]["candidate_id"] else "reject"
        )
        decision = {
            "slot_id": slot["slot_id"],
            "action": action,
            "actor": "editor@example.test",
            "decided_at": "2026-11-23T09:00:00Z",
        }
        if action == "replace":
            decision["replacement"] = copy.deepcopy(replacement)
        decisions.append(decision)
    return transition_decision_pack_review(pack, decisions, complete=True)


def test_actual_pipeline_carries_eligible_source_evidence_to_review():
    plan = _real_planning_slice()
    original_plan = copy.deepcopy(plan)
    assert "review_alternatives" in plan
    pack = build_decision_pack(plan)
    assert validate_decision_pack(pack)["status"] == "passed"
    assert plan == original_plan
    assert any(slot.get("alternatives") for slot in pack["slots"])

    score_tables = plan["fit_scores"]
    for slot in pack["slots"]:
        original_ids = {s["candidate_id"] for s in score_tables[slot["slot_id"]]}
        for alternative in slot["alternatives"]:
            candidate = alternative["candidate_id"]
            assert candidate in original_ids
            assert candidate != slot["proposal"]["candidate_id"]
            assert alternative["provenance"]["image_id"] == candidate
            assert alternative["placement"]["candidate_id"] == candidate
            assert alternative["placement"]["slot_id"] == slot["slot_id"]
            assert alternative["placement"]["output_path"].endswith(
                alternative["provenance"]["generated_filename"]
            )
            assert next(
                s for s in score_tables[slot["slot_id"]] if s["candidate_id"] == candidate
            )["decision"] != "rejected"


def test_one_click_selection_survives_review_and_read_only_diff(tmp_path):
    plan = _real_planning_slice()
    pack = build_decision_pack(plan)
    original = copy.deepcopy(pack)
    slot = next(s for s in pack["slots"] if s["alternatives"])
    replacement = slot["alternatives"][0]
    reviewed = _complete_review(pack, slot["slot_id"], replacement)

    assert pack == original
    assert validate_decision_pack(reviewed)["status"] == "passed"
    assert reviewed["application"] == {"status": "not_applied", "receipts": []}
    preview = preview_decision_pack(pack, reviewed)
    chosen = next(row for row in preview["slots"] if row["slot_id"] == slot["slot_id"])
    assert chosen["action"] == "replace"
    assert chosen["reviewed_candidate"] == replacement["candidate_id"]

    exported = tmp_path / "reviewed.json"
    exported.write_text(json.dumps(reviewed), encoding="utf-8")
    assert validate_decision_pack(json.loads(exported.read_text()))["status"] == "passed"


def test_unlisted_replacement_cannot_fabricate_owned_license():
    plan = _real_planning_slice()
    pack = build_decision_pack(plan)
    slot = next(s for s in pack["slots"] if s["alternatives"])
    fake = copy.deepcopy(slot["alternatives"][0])
    fake["provenance"]["license_status"] = "owned"
    with pytest.raises(ValueError, match="decision_pack_replacement_not_evidenced"):
        _complete_review(pack, slot["slot_id"], fake)


def test_hard_rejected_alternative_cannot_enter_review_inventory():
    pack = build_decision_pack(_real_planning_slice())
    slot = next(s for s in pack["slots"] if s["alternatives"])
    candidate = slot["alternatives"][0]["candidate_id"]
    for score in slot["candidates"]:
        if score["candidate_id"] == candidate:
            score["decision"] = "rejected"
    validation = validate_decision_pack(pack)
    assert validation["status"] == "failed"
    assert "decision_pack_alternative_rejected" in {
        error["code"] for error in validation["errors"]
    }


def test_legacy_packs_without_alternatives_remain_compatible():
    from actovisio_framework.testing.contracts import sample_decision_pack

    legacy = sample_decision_pack()
    assert "alternatives" not in legacy["slots"][0]
    assert validate_decision_pack(legacy)["status"] == "passed"


def test_empty_and_duplicate_evidenced_alternatives_are_guarded():
    pack = build_decision_pack(_real_planning_slice())
    slot = next(s for s in pack["slots"] if s["alternatives"])
    slot["alternatives"].append(copy.deepcopy(slot["alternatives"][0]))
    validation = validate_decision_pack(pack)
    assert "decision_pack_duplicate_alternative" in {
        error["code"] for error in validation["errors"]
    }
    slot["alternatives"] = [slot["proposal"]]
    validation = validate_decision_pack(pack)
    assert "decision_pack_alternative_is_proposal" in {
        error["code"] for error in validation["errors"]
    }


def test_explicit_credential_free_demo_is_valid_but_invented_modes_fail():
    plan = _real_planning_slice()
    assert plan["runtime"]["provider"]["mode"] == "demo"
    plan["runtime"]["provider"]["mode"] = "claiming-success"
    validation = validate_visual_plan(plan)
    assert validation["status"] == "failed"
    assert "invalid_provider_mode" in {
        error["code"] for error in validation["errors"]
    }


def test_gutenberg_style_one_click_roundtrip_uses_existing_cli_bridge(tmp_path):
    from actovisio_framework.app import cli

    plan = _real_planning_slice()
    plan_path = tmp_path / "plan.json"
    pack_path = tmp_path / "pending-pack.json"
    decisions_path = tmp_path / "review-decisions.json"
    reviewed_path = tmp_path / "reviewed.json"
    preview_path = tmp_path / "preview.md"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    assert cli.main([
        "review-pack", "--plan", str(plan_path), "--output", str(pack_path),
    ]) == 0
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    chosen_slot = next(slot for slot in pack["slots"] if slot["alternatives"])
    decisions = []
    for slot in pack["slots"]:
        action = (
            "replace" if slot["slot_id"] == chosen_slot["slot_id"]
            else "accept" if slot["proposal"]["candidate_id"] else "reject"
        )
        decision = {
            "slot_id": slot["slot_id"],
            "action": action,
            "actor": "editor@example.test",
            "decided_at": "2026-11-23T09:00:00Z",
        }
        if action == "replace":
            decision["replacement"] = copy.deepcopy(chosen_slot["alternatives"][0])
        decisions.append(decision)

    draft = {
        "kind": "pictovap.review-decisions",
        "schema_version": "1",
        "article_id": str(pack["article"]["id"]),
        "source_sha256": hashlib.sha256(pack_path.read_bytes()).hexdigest(),
        "decisions": decisions,
    }
    decisions_path.write_text(json.dumps(draft), encoding="utf-8")
    assert cli.main([
        "review-import", "--pack", str(pack_path),
        "--decisions", str(decisions_path),
        "--output", str(reviewed_path), "--preview", str(preview_path),
    ]) == 0
    reviewed = json.loads(reviewed_path.read_text())
    assert validate_decision_pack(reviewed)["status"] == "passed"
    assert reviewed["application"] == {"status": "not_applied", "receipts": []}
    assert "Editor Review Preview" in preview_path.read_text()

    # A malicious draft that upgrades source rights cannot be imported.
    replacement_entry = next(
        decision for decision in draft["decisions"] if decision["action"] == "replace"
    )
    replacement_entry["replacement"]["provenance"]["license_status"] = "owned"
    decisions_path.write_text(json.dumps(draft), encoding="utf-8")
    assert cli.main([
        "review-import", "--pack", str(pack_path),
        "--decisions", str(decisions_path),
        "--output", str(tmp_path / "forged.json"),
    ]) == 1
    assert not (tmp_path / "forged.json").exists()
