"""Tests for the portable, side-effect-free Decision Pack boundary."""

from copy import deepcopy

import pytest

from pictovap import build_decision_pack, validate_decision_pack


def _plan() -> dict:
    return {
        "visual_brief": {
            "article_id": "article-1",
            "article_title": "A visual article",
            "article_language": "en",
            "image_slots": [{"slot_id": "featured", "purpose": "featured_image"}],
        },
        "fit_scores": {
            "featured": [{
                "candidate_id": "img-1",
                "slot_id": "featured",
                "final_score": 9.2,
                "decision": "selected",
            }, {
                "candidate_id": "img-2",
                "slot_id": "featured",
                "final_score": 7.0,
                "decision": "needs_review",
            }]
        },
        "provenance_packs": [{
            "image_id": "img-1",
            "provider": "local",
            "slot_id": "featured",
            "generated_filename": "featured.jpg",
        }],
        "cms_placement": {
            "article_id": "article-1",
            "placements": [{"slot_id": "featured", "output_path": "images/featured.jpg"}],
        },
        "planning_diagnostics": {
            "slots_requested": 1,
            "slots_filled": 1,
            "coverage_ratio": 1.0,
        },
    }


def test_build_decision_pack_groups_existing_plan_evidence_by_slot():
    pack = build_decision_pack(_plan())

    assert pack["schema_version"] == "1"
    assert pack["review"] == {"status": "pending", "decisions": []}
    assert pack["application"] == {"status": "not_applied", "receipts": []}
    assert pack["slots"][0]["proposal"]["candidate_id"] == "img-1"
    assert pack["slots"][0]["proposal"]["placement"]["candidate_id"] == "img-1"
    assert pack["slots"][0]["proposal"]["placement"]["slot_id"] == "featured"
    assert validate_decision_pack(pack)["status"] == "passed"


def test_decision_pack_accepts_complete_editor_review_without_applying():
    pack = build_decision_pack(_plan())
    pack["review"] = {
        "status": "reviewed",
        "decisions": [{
            "slot_id": "featured",
            "action": "accept",
            "actor": "editor@example.test",
            "decided_at": "2026-09-02T12:00:00Z",
        }],
    }

    assert validate_decision_pack(pack)["status"] == "passed"


def test_decision_pack_rejects_incomplete_review_and_application_receipts():
    pack = build_decision_pack(_plan())
    pack["review"]["status"] = "reviewed"
    pack["application"]["receipts"] = [{"unexpected": True}]

    result = validate_decision_pack(pack)

    assert result["status"] == "failed"
    assert {item["code"] for item in result["errors"]} >= {
        "decision_pack_incomplete_review",
        "decision_pack_application_receipts",
    }


def test_decision_pack_requires_a_valid_source_plan():
    with pytest.raises(ValueError, match="must pass validation"):
        build_decision_pack({})


@pytest.mark.parametrize("missing", ["provenance", "placement"])
def test_build_decision_pack_requires_complete_proposal_evidence(missing):
    plan = _plan()
    if missing == "provenance":
        plan["provenance_packs"] = []
    else:
        plan["cms_placement"]["placements"] = []

    with pytest.raises(ValueError, match="semantically bound Decision Pack"):
        build_decision_pack(plan)


def test_build_decision_pack_rejects_provenance_for_a_different_candidate():
    plan = _plan()
    plan["provenance_packs"][0]["image_id"] = "img-2"

    with pytest.raises(ValueError, match="decision_pack_selected_candidate_binding"):
        build_decision_pack(plan)


def test_decision_pack_rejects_accept_when_proposal_has_no_bound_asset():
    pack = build_decision_pack(_plan())
    pack["slots"][0]["proposal"] = {
        "candidate_id": None,
        "provenance": None,
        "placement": None,
    }
    pending = validate_decision_pack(pack)
    pack["review"] = {
        "status": "reviewed",
        "decisions": [{
            "slot_id": "featured",
            "action": "accept",
            "actor": "editor@example.test",
            "decided_at": "2026-09-02T12:00:00Z",
        }],
    }

    result = validate_decision_pack(pack)

    assert pending["status"] == "passed"
    assert result["status"] == "failed"
    assert "decision_pack_accept_requires_proposal" in {
        item["code"] for item in result["errors"]
    }


def test_decision_pack_rejects_replace_without_replacement_evidence():
    pack = build_decision_pack(_plan())
    pack["review"] = {
        "status": "reviewed",
        "decisions": [{
            "slot_id": "featured",
            "action": "replace",
            "actor": "editor@example.test",
            "decided_at": "2026-09-02T12:00:00Z",
        }],
    }

    result = validate_decision_pack(pack)

    assert result["status"] == "failed"
    assert "decision_pack_replacement_required" in {
        item["code"] for item in result["errors"]
    }


def test_decision_pack_accepts_replace_with_atomic_replacement_evidence():
    pack = build_decision_pack(_plan())
    pack["review"] = {
        "status": "reviewed",
        "decisions": [{
            "slot_id": "featured",
            "action": "replace",
            "actor": "editor@example.test",
            "decided_at": "2026-09-02T12:00:00Z",
            "replacement": {
                "candidate_id": "img-2",
                "provenance": {
                    "image_id": "img-2",
                    "provider": "editor-library",
                    "slot_id": "featured",
                    "generated_filename": "replacement.jpg",
                },
                "placement": {
                    "candidate_id": "img-2",
                    "slot_id": "featured",
                    "output_path": "images/replacement.jpg",
                },
            },
        }],
    }

    assert validate_decision_pack(pack)["status"] == "passed"


def test_decision_pack_rejects_cross_bound_replacement_evidence():
    pack = build_decision_pack(_plan())
    replacement = {
        "candidate_id": "img-2",
        "provenance": {
            "image_id": "img-1",
            "provider": "editor-library",
            "slot_id": "featured",
            "generated_filename": "replacement.jpg",
        },
        "placement": {
            "candidate_id": "img-2",
            "slot_id": "featured",
            "output_path": "images/replacement.jpg",
        },
    }
    pack["review"] = {
        "status": "reviewed",
        "decisions": [{
            "slot_id": "featured",
            "action": "replace",
            "actor": "editor@example.test",
            "decided_at": "2026-09-02T12:00:00Z",
            "replacement": deepcopy(replacement),
        }],
    }

    result = validate_decision_pack(pack)

    assert result["status"] == "failed"
    assert "decision_pack_provenance_candidate_binding" in {
        item["code"] for item in result["errors"]
    }


def test_decision_pack_requires_unambiguous_final_assignment():
    pack = build_decision_pack(_plan())
    pack["slots"][0]["candidates"][1]["decision"] = "selected"

    ambiguous = validate_decision_pack(pack)
    pack["slots"][0]["evidence"] = [{
        "slot_id": "featured",
        "candidate_id": "img-1",
        "assignment": "assigned",
    }]
    assigned = validate_decision_pack(pack)

    assert ambiguous["status"] == "failed"
    assert "decision_pack_ambiguous_selected_candidate" in {
        item["code"] for item in ambiguous["errors"]
    }
    assert assigned["status"] == "passed"


def test_build_decision_pack_rejects_placement_for_a_different_asset():
    plan = _plan()
    plan["cms_placement"]["placements"][0]["output_path"] = "images/other.jpg"

    with pytest.raises(ValueError, match="decision_pack_placement_asset_binding"):
        build_decision_pack(plan)
