"""Tests for the portable, side-effect-free Decision Pack boundary."""

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
            }]
        },
        "provenance_packs": [{
            "image_id": "img-1",
            "provider": "local",
            "slot_id": "featured",
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
