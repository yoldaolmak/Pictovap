"""Tests for the read-only visual-plan audit boundary."""

import json
import subprocess
import sys

from pictovap.audit import audit_visual_plan, render_audit_markdown


def valid_plan() -> dict:
    return {
        "visual_brief": {
            "article_title": "A visual article",
            "image_slots": [{"slot_id": "featured", "purpose": "featured_image"}],
        },
        "fit_scores": {"featured": [{
            "candidate_id": "img-1", "slot_id": "featured", "final_score": 9.2,
            "decision": "selected",
        }]},
        "provenance_packs": [{
            "image_id": "img-1", "provider": "local", "slot_id": "featured",
            "license_status": "cc0",
        }],
        "cms_placement": {"article_id": "article-1", "placements": [{
            "slot_id": "featured", "output_path": "images/featured.jpg",
            "alt_text": "A clear editorial image",
        }]},
        "planning_diagnostics": {"slots_requested": 1, "slots_filled": 1, "coverage_ratio": 1.0},
    }


def test_complete_plan_passes_audit():
    result = audit_visual_plan(valid_plan())

    assert result["status"] == "passed"
    assert result["metrics"]["accessible_placements"] == 1
    assert result["checks"]["provenance"]["status"] == "passed"


def test_incomplete_editorial_plan_is_warning_then_strict_failure():
    plan = valid_plan()
    del plan["cms_placement"]["placements"][0]["alt_text"]
    plan["fit_scores"]["featured"][0]["decision"] = "needs_review"

    relaxed = audit_visual_plan(plan)
    strict = audit_visual_plan(plan, strict=True)

    assert relaxed["status"] == "warning"
    assert relaxed["checks"]["accessibility"]["status"] == "warning"
    assert relaxed["checks"]["review_queue"]["status"] == "warning"
    assert strict["status"] == "failed"


def test_duplicate_selection_is_machine_readable_and_renderable():
    plan = valid_plan()
    plan["visual_brief"]["image_slots"].append({"slot_id": "section_0"})
    plan["fit_scores"]["section_0"] = [{
        "candidate_id": "img-1", "slot_id": "section_0", "final_score": 8.1,
        "decision": "selected",
    }]
    result = audit_visual_plan(plan)
    markdown = render_audit_markdown(result)

    assert result["checks"]["duplicate_selection"]["status"] == "warning"
    assert "img-1" in markdown
    assert "Pictovap Plan Audit" in markdown


def test_audit_cli_emits_json_and_allows_warning_without_strict_mode(tmp_path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(valid_plan()), encoding="utf-8")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    del plan["cms_placement"]["placements"][0]["alt_text"]
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "pictovap", "audit", "--plan", str(plan_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout)["checks"]["accessibility"]["status"] == "warning"

    strict_result = subprocess.run(
        [sys.executable, "-m", "pictovap", "audit", "--plan", str(plan_path), "--strict"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert strict_result.returncode == 1
