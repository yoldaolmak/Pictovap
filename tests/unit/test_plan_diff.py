"""Tests for deterministic, side-effect-free visual-plan comparison."""

import copy
import json
import subprocess
import sys

import pytest

from pictovap import diff_visual_plans
from pictovap.plan_diff import plan_diff_to_json, render_plan_diff_markdown


def sample_plan() -> dict:
    constraints = [{
        "code": "license_declared",
        "kind": "hard",
        "requirement": "candidate declares a usable license",
    }]
    return {
        "visual_brief": {
            "article_id": "article-1",
            "article_title": "Coastal rail guide",
            "article_language": "en",
            "topic": "coastal rail",
            "image_slots": [
                {
                    "slot_id": "featured",
                    "purpose": "featured_image",
                    "preferred_type": "landscape",
                    "section_excerpt": "Coastal rail guide",
                },
                {
                    "slot_id": "section_0",
                    "purpose": "inline_after_route",
                    "preferred_type": "any",
                    "target_heading": "Route",
                    "section_excerpt": "Follow the coast by train.",
                },
            ],
        },
        "profile": {
            "id": "publisher-1",
            "brand": "Example Publisher",
            "cms_type": "wordpress",
            "language": "en",
        },
        "fit_scores": {
            "featured": [{
                "candidate_id": "img-1",
                "slot_id": "featured",
                "final_score": 9.2,
                "decision": "selected",
                "human_reason": "Best editorial fit",
            }],
            "section_0": [{
                "candidate_id": "img-2",
                "slot_id": "section_0",
                "final_score": 8.4,
                "decision": "selected",
                "human_reason": "Matches the route section",
            }],
        },
        "provenance_packs": [
            {
                "image_id": "img-1",
                "provider": "local",
                "source_type": "local",
                "slot_id": "featured",
                "license_status": "cc0",
                "content_hash": "hash-1",
                "generated_alt_text": "A coastal railway",
            },
            {
                "image_id": "img-2",
                "provider": "local",
                "source_type": "local",
                "slot_id": "section_0",
                "license_status": "cc0",
                "content_hash": "hash-2",
                "generated_alt_text": "A train beside the sea",
            },
        ],
        "cms_placement": {
            "article_id": "article-1",
            "placements": [
                {
                    "slot_id": "featured",
                    "output_path": "images/featured.webp",
                    "placement_strategy": "featured",
                    "image_role": "featured",
                    "alt_text": "A coastal railway",
                },
                {
                    "slot_id": "section_0",
                    "output_path": "images/route.webp",
                    "target_section": "Route",
                    "placement_strategy": "after_heading",
                    "image_role": "content",
                    "alt_text": "A train beside the sea",
                },
            ],
        },
        "planning_diagnostics": {
            "slots_requested": 2,
            "slots_filled": 2,
            "coverage_ratio": 1.0,
            "total_score": 17.6,
            "warnings": [],
        },
        "intent_proof": {
            "graph": {
                "slots": [
                    {
                        "slot_id": "featured",
                        "role": "featured",
                        "purpose": "featured_image",
                        "target_heading": "",
                        "query_terms": ["coastal", "rail"],
                        "constraints": constraints,
                    },
                    {
                        "slot_id": "section_0",
                        "role": "inline",
                        "purpose": "inline_after_route",
                        "target_heading": "Route",
                        "query_terms": ["coastal", "rail", "route"],
                        "constraints": constraints,
                    },
                ],
            },
            "ledger": [
                {
                    "slot_id": "featured",
                    "candidate_id": "img-1",
                    "decision": "selected",
                    "assignment": "assigned",
                    "reason_codes": ["assigned_by_global_policy"],
                    "evidence": {"provider": "local", "license": "cc0"},
                },
                {
                    "slot_id": "section_0",
                    "candidate_id": "img-2",
                    "decision": "selected",
                    "assignment": "assigned",
                    "reason_codes": ["assigned_by_global_policy"],
                    "evidence": {"provider": "local", "license": "cc0"},
                },
            ],
        },
    }


def changed_plan() -> dict:
    plan = copy.deepcopy(sample_plan())
    plan["visual_brief"]["topic"] = "night trains"
    plan["visual_brief"]["image_slots"][1]["preferred_type"] = "portrait"
    plan["profile"]["id"] = "publisher-2"
    plan["fit_scores"]["featured"][0]["final_score"] = 8.7
    plan["fit_scores"]["section_1"] = [{
        "candidate_id": "img-3",
        "slot_id": "section_1",
        "final_score": 8.0,
        "decision": "selected",
        "human_reason": "Matches night travel",
    }]
    plan["provenance_packs"][0]["image_id"] = "img-2"
    plan["cms_placement"]["placements"][0]["caption"] = "Night train"
    plan["planning_diagnostics"]["total_score"] = 17.1
    plan["intent_proof"]["graph"]["slots"][0]["query_terms"] = ["night", "trains"]
    plan["intent_proof"]["ledger"][0]["evidence"]["license"] = "cc-by"
    return plan


def test_identical_plans_produce_a_stable_empty_diff():
    plan = sample_plan()

    result = diff_visual_plans(plan, copy.deepcopy(plan))

    assert result["schema_version"] == "1"
    assert result["status"] == "unchanged"
    assert result["change_sources"] == []
    assert result["summary"]["total_changes"] == 0
    assert result["identity"]["same_article"] is True


def test_article_identity_change_is_counted_as_article_drift():
    before = sample_plan()
    after = copy.deepcopy(before)
    after["visual_brief"]["article_id"] = "article-2"
    after["cms_placement"]["article_id"] = "article-2"

    result = diff_visual_plans(before, after)

    assert result["status"] == "changed"
    assert result["change_sources"] == ["article"]
    assert result["identity"]["same_article"] is False
    assert result["summary"]["article_identity_changed"] == 1
    assert result["summary"]["total_changes"] == 1


def test_diff_attributes_article_profile_candidate_policy_and_cms_changes():
    result = diff_visual_plans(sample_plan(), changed_plan())

    assert result["status"] == "changed"
    assert result["change_sources"] == [
        "article",
        "profile",
        "candidates",
        "policy",
        "cms_placement",
    ]
    assert result["candidate_pool"] == {"added": ["img-3"], "removed": []}
    assert result["summary"]["article_fields_changed"] == 1
    assert result["summary"]["profile_fields_changed"] == 1
    assert result["summary"]["slots_changed"] == 1
    assert result["summary"]["evaluations_changed"] == 2
    assert result["summary"]["selections_changed"] == 1
    assert result["summary"]["placements_changed"] == 1
    assert result["summary"]["intent_slots_changed"] == 1
    assert result["summary"]["intent_ledger_entries_changed"] == 1
    assert result["summary"]["diagnostics_fields_changed"] == 1


def test_json_and_markdown_renderers_are_deterministic_and_reviewable():
    result = diff_visual_plans(sample_plan(), changed_plan())

    serialized = plan_diff_to_json(result)
    markdown = render_plan_diff_markdown(result)

    assert serialized.endswith("\n")
    assert json.loads(serialized) == result
    assert "# Pictovap Plan Diff" in markdown
    assert "Candidate Evaluation Changes" in markdown
    assert "`topic`" in markdown
    assert "night trains" in markdown


def test_diff_rejects_non_object_inputs():
    with pytest.raises(TypeError, match="JSON objects"):
        diff_visual_plans([], sample_plan())


def test_cli_supports_markdown_output_and_ci_fail_on_change(tmp_path):
    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    output_path = tmp_path / "diff.md"
    before_path.write_text(json.dumps(sample_plan()), encoding="utf-8")
    after_path.write_text(json.dumps(changed_plan()), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pictovap",
            "diff",
            "--before",
            str(before_path),
            "--after",
            str(after_path),
            "--output",
            str(output_path),
            "--fail-on-change",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert output_path.read_text(encoding="utf-8") == result.stdout
    assert "# Pictovap Plan Diff" in result.stdout


def test_cli_returns_zero_for_change_without_ci_gate(tmp_path):
    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    before_path.write_text(json.dumps(sample_plan()), encoding="utf-8")
    after_path.write_text(json.dumps(changed_plan()), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pictovap",
            "diff",
            "--before",
            str(before_path),
            "--after",
            str(after_path),
            "--format",
            "json",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "changed"
