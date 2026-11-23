"""Gutenberg review handoff: real Core validation, never WordPress writes."""

import hashlib
import json
from copy import deepcopy

from pictovap import sample_visual_plan, validate_decision_pack
from pictovap.app import cli


def _prepare(tmp_path):
    plan = sample_visual_plan(article_id="42")
    plan["visual_brief"]["article_title"] = "A Gutenberg weekend guide"
    plan_path = tmp_path / "plan.json"
    pack_path = tmp_path / "pending.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    assert cli.main([
        "review-pack", "--plan", str(plan_path), "--output", str(pack_path),
    ]) == 0
    return plan_path, pack_path


def _draft(pack_path, action="accept", actor="editor"):
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    return {
        "kind": "pictovap.review-decisions",
        "schema_version": "1",
        "article_id": str(pack["article"]["id"]),
        "source_sha256": hashlib.sha256(pack_path.read_bytes()).hexdigest(),
        "decisions": [{
            "slot_id": slot["slot_id"],
            "action": action,
            "actor": actor,
            "decided_at": "2026-11-23T08:00:00Z",
        } for slot in pack["slots"]],
    }


def _import(tmp_path, pack_path, draft, suffix=""):
    draft_path = tmp_path / f"decisions{suffix}.json"
    reviewed_path = tmp_path / f"reviewed{suffix}.json"
    preview_path = tmp_path / f"preview{suffix}.md"
    draft_path.write_text(json.dumps(draft), encoding="utf-8")
    code = cli.main([
        "review-import", "--pack", str(pack_path),
        "--decisions", str(draft_path),
        "--output", str(reviewed_path),
        "--preview", str(preview_path),
    ])
    return code, reviewed_path, preview_path


def test_gutenberg_review_roundtrip_is_verified_in_core(tmp_path, monkeypatch):
    def forbidden_cms(*args, **kwargs):
        raise AssertionError("Review unexpectedly attempted a CMS action")

    monkeypatch.setattr(cli.PipelineRunner, "publish", forbidden_cms)
    plan_path, pack_path = _prepare(tmp_path)
    source_bytes = pack_path.read_bytes()
    draft = _draft(pack_path)
    code, reviewed_path, preview_path = _import(tmp_path, pack_path, draft)

    assert code == 0
    assert pack_path.read_bytes() == source_bytes
    reviewed = json.loads(reviewed_path.read_text(encoding="utf-8"))
    assert validate_decision_pack(reviewed)["status"] == "passed"
    assert reviewed["review"]["status"] == "reviewed"
    assert reviewed["review"]["decisions"][0]["actor"] == "editor"
    assert reviewed["application"] == {"status": "not_applied", "receipts": []}
    assert "CMS write" in preview_path.read_text(encoding="utf-8")
    assert json.loads(plan_path.read_text(encoding="utf-8"))["visual_brief"]["article_id"] == "42"


def test_source_pack_fingerprint_prevents_mismatched_or_modified_proposal(tmp_path, capsys):
    _, pack_path = _prepare(tmp_path)
    draft = _draft(pack_path)
    old = json.loads(pack_path.read_text(encoding="utf-8"))
    old["article"]["title"] = "Quietly changed after editor review"
    pack_path.write_text(json.dumps(old), encoding="utf-8")
    code, output_path, preview_path = _import(tmp_path, pack_path, draft)

    assert code == 1
    assert not output_path.exists()
    assert not preview_path.exists()
    assert "fingerprint" in capsys.readouterr().err


def test_import_rejects_forged_application_in_source(tmp_path):
    _, pack_path = _prepare(tmp_path)
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    pack["application"]["status"] = "completed"
    pack["application"]["receipts"] = [{"fake": "applied"}]
    pack_path.write_text(json.dumps(pack), encoding="utf-8")
    draft = _draft(pack_path)
    code, output_path, _ = _import(tmp_path, pack_path, draft)

    assert code == 1
    assert not output_path.exists()


def test_import_rejects_missing_actor_and_unknown_slot(tmp_path):
    _, pack_path = _prepare(tmp_path)
    draft = _draft(pack_path)
    missing = deepcopy(draft)
    missing["decisions"][0]["actor"] = ""
    result, output, _ = _import(tmp_path, pack_path, missing, suffix="-missing")
    assert result == 1 and not output.exists()

    unknown = deepcopy(draft)
    unknown["decisions"][0]["slot_id"] = "not-the-source-slot"
    result, output, _ = _import(tmp_path, pack_path, unknown, suffix="-wrong")
    assert result == 1 and not output.exists()


def test_import_rejects_unsigned_article_swap(tmp_path):
    _, pack_path = _prepare(tmp_path)
    draft = _draft(pack_path)
    draft["article_id"] = "999"
    result, output, _ = _import(tmp_path, pack_path, draft)
    assert result == 1
    assert not output.exists()


def test_import_cannot_overwrite_review_inputs_or_existing_output(tmp_path):
    _, pack_path = _prepare(tmp_path)
    draft = _draft(pack_path)
    code, output, _ = _import(tmp_path, pack_path, draft)
    assert code == 0
    original_bytes = output.read_bytes()

    draft_path = tmp_path / "same-draft.json"
    draft_path.write_text(json.dumps(draft), encoding="utf-8")
    assert cli.main([
        "review-import", "--pack", str(pack_path),
        "--decisions", str(draft_path), "--output", str(output),
    ]) == 1
    assert output.read_bytes() == original_bytes
    assert cli.main([
        "review-import", "--pack", str(pack_path),
        "--decisions", str(draft_path), "--output", str(pack_path),
    ]) == 1


def test_review_pack_requires_valid_source_plan_and_refuses_overwrite(tmp_path):
    source = tmp_path / "bad-plan.json"
    dest = tmp_path / "pending.json"
    source.write_text("{}", encoding="utf-8")
    assert cli.main(["review-pack", "--plan", str(source), "--output", str(dest)]) == 1
    assert not dest.exists()
    source.write_text(json.dumps(sample_visual_plan("42")), encoding="utf-8")
    assert cli.main(["review-pack", "--plan", str(source), "--output", str(dest)]) == 0
    original = dest.read_bytes()
    assert cli.main(["review-pack", "--plan", str(source), "--output", str(dest)]) == 1
    assert dest.read_bytes() == original
