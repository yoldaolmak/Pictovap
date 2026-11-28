"""End-to-end, offline editor review journey and negative rights/authority tests."""

import json
from copy import deepcopy

import pytest

from actovisio_framework import build_decision_pack, sample_decision_pack, sample_visual_plan
from actovisio_framework.app import cli
from actovisio_framework.decision_pack import transition_decision_pack_review, validate_decision_pack
from actovisio_framework.review import preview_decision_pack, render_review_preview


def _review(pack, action, replacement=None):
    decision = {
        "slot_id": "featured",
        "action": action,
        "actor": "editor@example.test",
        "decided_at": "2026-11-22T20:00:00+00:00",
    }
    if replacement is not None:
        decision["replacement"] = replacement
    return transition_decision_pack_review(pack, [decision], complete=True)


def _replacement():
    return {
        "candidate_id": "candidate-2",
        "provenance": {
            "image_id": "candidate-2",
            "provider": "local",
            "slot_id": "featured",
            "generated_filename": "replacement.webp",
            "license_status": "unknown",
        },
        "placement": {
            "candidate_id": "candidate-2",
            "slot_id": "featured",
            "output_path": "images/replacement.webp",
        },
    }


def _with_alternative():
    pack = sample_decision_pack()
    pack["slots"][0]["candidates"].append({
        "candidate_id": "candidate-2",
        "slot_id": "featured",
        "final_score": 6.0,
        "decision": "needs_review",
    })
    return pack


def test_preview_accept_preserves_evidence_and_does_not_claim_cms_execution():
    pack = sample_decision_pack()
    original = deepcopy(pack)
    reviewed = _review(pack, "accept")

    comparison = preview_decision_pack(pack, reviewed)
    markdown = render_review_preview(comparison)

    assert pack == original
    assert comparison["summary"] == {
        "slots": 1,
        "decisions": 1,
        "images_kept": 1,
        "rights_unresolved": 1,
    }
    assert comparison["slots"][0]["reviewed_candidate"] == "candidate-contract-1"
    assert comparison["application_status"] == "not_applied"
    assert "no CMS write" in markdown
    assert "does not grant image rights" in markdown


def test_preview_reject_removes_image_from_editorial_selection():
    pack = sample_decision_pack()
    reviewed = _review(pack, "reject")
    comparison = preview_decision_pack(pack, reviewed)

    assert comparison["slots"][0]["action"] == "reject"
    assert comparison["slots"][0]["proposed_candidate"] == "candidate-contract-1"
    assert comparison["slots"][0]["reviewed_candidate"] is None
    assert comparison["summary"]["images_kept"] == 0


def test_review_preview_rejects_tampered_original_evidence():
    pack = sample_decision_pack()
    reviewed = _review(pack, "accept")
    reviewed["slots"][0]["proposal"]["candidate_id"] = "other"

    with pytest.raises(ValueError, match="invalid|changed proposal"):
        preview_decision_pack(pack, reviewed)


def test_review_preview_rejects_fake_application_receipt():
    pack = sample_decision_pack()
    reviewed = _review(pack, "accept")
    reviewed["application"]["status"] = "completed"

    with pytest.raises(ValueError, match="invalid"):
        preview_decision_pack(pack, reviewed)


def test_replacement_requires_non_rejected_scored_candidate_and_bound_evidence():
    pack = _with_alternative()
    replacement = _replacement()
    reviewed = _review(pack, "replace", replacement)

    assert validate_decision_pack(reviewed)["status"] == "passed"
    summary = preview_decision_pack(pack, reviewed)
    assert summary["slots"][0]["reviewed_candidate"] == "candidate-2"
    assert summary["summary"]["rights_unresolved"] == 1

    rejected = deepcopy(pack)
    rejected["slots"][0]["candidates"][1]["decision"] = "rejected"
    with pytest.raises(ValueError, match="decision_pack_replacement_rejected_candidate"):
        _review(rejected, "replace", replacement)


def test_interactive_review_writes_valid_roundtrip_without_mutating_plan(
    tmp_path, monkeypatch, capsys,
):
    plan = sample_visual_plan()
    source = tmp_path / "plan.json"
    output = tmp_path / "reviewed.json"
    preview = tmp_path / "preview.md"
    source.write_text(json.dumps(plan), encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "a")

    result = cli.main([
        "review", "--plan", str(source),
        "--actor", "editor@example.test",
        "--output", str(output),
        "--preview", str(preview),
    ])

    assert result == 0
    assert json.loads(source.read_text(encoding="utf-8")) == plan
    reviewed = json.loads(output.read_text(encoding="utf-8"))
    assert validate_decision_pack(reviewed)["status"] == "passed"
    assert reviewed["review"]["status"] == "reviewed"
    assert reviewed["application"] == {"status": "not_applied", "receipts": []}
    assert preview.read_text(encoding="utf-8").startswith("# Pictovap")
    assert "unknown" in capsys.readouterr().out


def test_cli_can_replay_a_preview_from_saved_plan_and_review(tmp_path, monkeypatch, capsys):
    plan_file = tmp_path / "plan.json"
    review_file = tmp_path / "review.json"
    plan_file.write_text(json.dumps(sample_visual_plan()), encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "j")
    assert cli.main([
        "review", "--plan", str(plan_file),
        "--actor", "reviewer", "--output", str(review_file),
    ]) == 0
    capsys.readouterr()

    result = cli.main([
        "review-preview", "--plan", str(plan_file),
        "--reviewed", str(review_file), "--format", "json",
    ])

    assert result == 0
    comparison = json.loads(capsys.readouterr().out)
    assert comparison["slots"][0]["action"] == "reject"
    assert comparison["application_status"] == "not_applied"


def test_interactive_review_can_use_alternative_with_supplied_provenance(
    tmp_path, monkeypatch,
):
    proposal = _with_alternative()
    input_file = tmp_path / "pending.json"
    evidence_file = tmp_path / "evidence.json"
    reviewed_file = tmp_path / "reviewed.json"
    input_file.write_text(json.dumps(proposal), encoding="utf-8")
    evidence_file.write_text(json.dumps(_replacement()), encoding="utf-8")
    actions = iter(["r", str(evidence_file)])
    monkeypatch.setattr("builtins.input", lambda _: next(actions))

    assert cli.main([
        "review", "--pack", str(input_file),
        "--actor", "editor", "--output", str(reviewed_file),
    ]) == 0
    reviewed = json.loads(reviewed_file.read_text(encoding="utf-8"))
    assert reviewed["review"]["decisions"][0]["replacement"]["candidate_id"] == "candidate-2"
    assert preview_decision_pack(proposal, reviewed)["summary"]["rights_unresolved"] == 1


def test_cancelled_review_and_path_collision_leave_no_artifacts(
    tmp_path, monkeypatch, capsys,
):
    source = tmp_path / "plan.json"
    source.write_text(json.dumps(sample_visual_plan()), encoding="utf-8")
    target = tmp_path / "review.json"
    monkeypatch.setattr("builtins.input", lambda _: "q")
    assert cli.main([
        "review", "--plan", str(source),
        "--actor", "editor", "--output", str(target),
    ]) == 1
    assert not target.exists()

    assert cli.main([
        "review", "--plan", str(source),
        "--actor", "editor", "--output", str(source),
    ]) == 1
    assert json.loads(source.read_text(encoding="utf-8")) == sample_visual_plan()
    assert "Review not saved" in capsys.readouterr().err


def test_review_preview_rejects_different_article_even_when_valid():
    first = sample_decision_pack()
    other = sample_decision_pack(article_id="other-article")
    reviewed = _review(other, "reject")

    with pytest.raises(ValueError, match="changed proposal"):
        preview_decision_pack(first, reviewed)


def test_editor_preview_escapes_table_controls():
    pack = sample_decision_pack()
    pack["slots"][0]["slot_id"] = "heading|featured"
    pack["slots"][0]["candidates"][0]["slot_id"] = "heading|featured"
    pack["slots"][0]["proposal"]["provenance"]["slot_id"] = "heading|featured"
    pack["slots"][0]["proposal"]["placement"]["slot_id"] = "heading|featured"
    reviewed = transition_decision_pack_review(pack, [{
        "slot_id": "heading|featured",
        "action": "reject",
        "actor": "editor",
        "decided_at": "2026-11-22T20:00:00+00:00",
    }], complete=True)
    rendered = render_review_preview(preview_decision_pack(pack, reviewed))

    assert r"heading\|featured" in rendered


def test_review_does_not_echo_signed_source_url(tmp_path, monkeypatch, capsys):
    pack = sample_decision_pack()
    pack["slots"][0]["proposal"]["provenance"]["source_url"] = (
        "https://media.example.test/image.jpg?signature=demo-secret"
    )
    source = tmp_path / "pending.json"
    dest = tmp_path / "reviewed.json"
    source.write_text(json.dumps(pack), encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "a")

    assert cli.main([
        "review", "--pack", str(source),
        "--actor", "editor", "--output", str(dest),
    ]) == 0
    assert "demo-secret" not in capsys.readouterr().out
