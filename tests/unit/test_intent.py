import json
import subprocess
import sys
from pathlib import Path

from pictovap.api import create_visual_plan
from pictovap import validate_intent_proof, validate_visual_plan
from pictovap.testing.contracts import sample_candidate


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTICLE = REPO_ROOT / "tests" / "corpus" / "travel.md"


class IntentFixtureProvider:
    def search_candidates(self, query, count):
        return [
            {
                **sample_candidate(f"intent-{index}"),
                "filename": f"intent-{index}.webp",
                "provider": "local",
                "source_type": "local",
                "local_path": f"/tmp/intent-{index}.webp",
                "source_url": None,
                "keywords": ["coastal", "rail", "travel", "route", "article"],
            }
            for index in range(count)
        ]


def test_plan_contains_proof_carrying_intent_graph_and_ledger():
    plan = create_visual_plan(str(ARTICLE), provider_adapter=IntentFixtureProvider())

    proof = plan["intent_proof"]
    assert proof["schema_version"] == "1"
    assert proof["graph"]["compiler"] == "pictovap.visual-intent"
    assert len(proof["graph"]["slots"]) == 4
    assert proof["summary"]["evaluations"] == len(proof["ledger"])
    assert any(entry["decision"] == "selected" for entry in proof["ledger"])
    assert all("hard_constraints" in entry and "evidence" in entry for entry in proof["ledger"])


def test_generated_intent_proof_passes_structural_validation():
    plan = create_visual_plan(str(ARTICLE), provider_adapter=IntentFixtureProvider())

    result = validate_intent_proof(
        plan["intent_proof"],
        expected_slot_ids=[slot["slot_id"] for slot in plan["visual_brief"]["image_slots"]],
    )

    assert result["status"] == "passed"
    assert result["errors"] == []
    assert validate_visual_plan(plan)["checks"]["intent_proof"]["status"] == "passed"


def test_intent_validator_reports_stable_codes_for_corruption():
    plan = create_visual_plan(str(ARTICLE), provider_adapter=IntentFixtureProvider())
    proof = json.loads(json.dumps(plan["intent_proof"]))
    proof["schema_version"] = "999"
    proof["graph"]["slots"][0]["slot_id"] = proof["graph"]["slots"][1]["slot_id"]
    proof["summary"]["selected"] += 1

    result = validate_intent_proof(proof)
    codes = {item["code"] for item in result["errors"]}

    assert result["status"] == "failed"
    assert {"intent_schema_version", "intent_duplicate_slot", "intent_summary_mismatch"} <= codes


def test_explain_cli_renders_intent_proof(tmp_path):
    plan_path = tmp_path / "plan.json"
    plan = create_visual_plan(str(ARTICLE), provider_adapter=IntentFixtureProvider())
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "pictovap", "explain", "--plan", str(plan_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "# Visual Intent Explanation" in result.stdout
    assert "assigned_by_global_policy" in result.stdout
