"""Tests for the public visual-plan validation boundary."""

import json
import subprocess
import sys

from pictovap import validate_visual_plan


def valid_plan() -> dict:
    return {
        "visual_brief": {
            "article_title": "A visual article",
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


def test_valid_plan_passes_without_network_or_side_effects():
    result = validate_visual_plan(valid_plan())

    assert result["status"] == "passed"
    assert result["errors"] == []
    assert result["summary"] == {"errors": 0, "warnings": 0}


def test_missing_contract_fields_are_machine_readable():
    result = validate_visual_plan({"visual_brief": {"image_slots": []}})

    assert result["status"] == "failed"
    assert {item["code"] for item in result["errors"]} >= {
        "value_required", "object_required", "list_required"
    }
    assert all(set(item) == {"code", "path", "message"} for item in result["errors"])


def test_strict_mode_promotes_recommendations_to_failures():
    plan = valid_plan()
    del plan["planning_diagnostics"]

    relaxed = validate_visual_plan(plan)
    strict = validate_visual_plan(plan, strict=True)

    assert relaxed["status"] == "passed"
    assert relaxed["warnings"]
    assert strict["status"] == "failed"
    assert any(item["code"].startswith("strict_") for item in strict["errors"])


def test_validate_cli_returns_json_and_nonzero_for_invalid_plan(tmp_path):
    plan_path = tmp_path / "invalid.json"
    plan_path.write_text(json.dumps({"visual_brief": {"article_title": ""}}), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "pictovap", "validate", "--plan", str(plan_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert payload["summary"]["errors"] > 0
