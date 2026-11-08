from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pictovap.app.runtime import PipelineRunner
from pictovap.core.primitives import FitScore, VisualBrief
from pictovap.core.profile import PublisherProfile
from pictovap.core.selection import SelectionPolicy, select_assignments
from pictovap.core.sources import (
    NOT_EVALUABLE,
    OBSERVED,
    UNKNOWN,
    SourceAttempt,
)
from pictovap.core.states import (
    CandidateDecision,
    DoctorStatus,
    MediaGuardStatus,
    MediaIntegrityState,
    PlanDiffStatus,
    PublishMode,
    PublishStatus,
    ReviewAction,
    ReviewStatus,
    aggregate_check_status,
    guard_status_for_state,
    resolve_publish_status,
)
from pictovap.decision_pack import transition_decision_pack_review
from pictovap.intent import compile_intent_proof
from pictovap.intent_validation import validate_intent_proof
from pictovap.services.wordpress import WordPressUploader
from pictovap.testing import sample_decision_pack, sample_visual_plan
from pictovap.utils.config import load_project_env, reset_project_env
from pictovap.validation import validate_visual_plan


# ---------------------------------------------------------------------------
# 1. SourceAttempt state invariants and validate_visual_plan checks
# ---------------------------------------------------------------------------
def test_source_attempt_invariants_reject_corrupt_states() -> None:
    # Valid attempts
    obs = SourceAttempt(source="unsplash", state=OBSERVED, candidates=3)
    assert obs.state == "observed"

    # Reject invalid state
    with pytest.raises(ValueError, match="Invalid SourceAttempt state"):
        SourceAttempt(source="bad", state="corrupt_state")

    # Reject negative candidates
    with pytest.raises(ValueError, match="candidates cannot be negative"):
        SourceAttempt(source="local", state=OBSERVED, candidates=-1)

    # Reject observed carrying error_type
    with pytest.raises(ValueError, match="Observed SourceAttempt cannot carry error_type"):
        SourceAttempt(source="unsplash", state=OBSERVED, candidates=2, error_type="RuntimeError")

    # Reject not_evaluable with candidates > 0
    with pytest.raises(ValueError, match="not_evaluable SourceAttempt must have 0 candidates"):
        SourceAttempt(source="unsplash", state=NOT_EVALUABLE, candidates=1, reason="adapter_error")

    # Reject not_evaluable missing reason
    with pytest.raises(ValueError, match="not_evaluable SourceAttempt requires a reason"):
        SourceAttempt(source="unsplash", state=NOT_EVALUABLE, candidates=0, reason="")

    # Reject unknown with candidates > 0
    with pytest.raises(ValueError, match="unknown SourceAttempt must have 0 candidates"):
        SourceAttempt(source="unsplash", state=UNKNOWN, candidates=1, reason="count_satisfied")

    # Reject unknown with error_type
    with pytest.raises(ValueError, match="unknown SourceAttempt cannot carry error_type"):
        SourceAttempt(source="unsplash", state=UNKNOWN, candidates=0, reason="skipped", error_type="KeyError")

    # Reject unknown missing reason
    with pytest.raises(ValueError, match="unknown SourceAttempt requires a reason"):
        SourceAttempt(source="unsplash", state=UNKNOWN, candidates=0, reason=None)


def test_validate_visual_plan_catches_corrupt_runtime_sources() -> None:
    plan = sample_visual_plan()

    # Valid plan passes runtime check
    plan["runtime"] = {
        "provider": {"mode": "fallback", "name": None},
        "sources": [{"source": "local", "state": "observed", "candidates": 2}],
    }
    res = validate_visual_plan(plan)
    assert res["status"] == "passed"
    assert res["checks"]["runtime"]["status"] == "passed"

    # Corrupt source state
    plan["runtime"]["sources"] = [{"source": "bad", "state": "invalid_mode", "candidates": 0}]
    res = validate_visual_plan(plan)
    assert res["status"] == "failed"
    assert any(e["code"] == "invalid_source_state" for e in res["errors"])

    # Corrupt invariant: observed with error_type
    plan["runtime"]["sources"] = [
        {"source": "local", "state": "observed", "candidates": 1, "error_type": "ValueError"}
    ]
    res = validate_visual_plan(plan)
    assert res["status"] == "failed"
    assert any(e["code"] == "invalid_source_invariant" for e in res["errors"])

    # Corrupt provider mode
    plan["runtime"]["provider"]["mode"] = "invalid_provider_mode"
    plan["runtime"]["sources"] = [{"source": "local", "state": "observed", "candidates": 1}]
    res = validate_visual_plan(plan)
    assert res["status"] == "failed"
    assert any(e["code"] == "invalid_provider_mode" for e in res["errors"])


# ---------------------------------------------------------------------------
# 2. FitScore, SelectionPolicy, and Intent Validation
# ---------------------------------------------------------------------------
def test_fit_score_rejects_illegal_decision() -> None:
    # Valid
    score = FitScore(candidate_id="c1", decision="selected")
    assert score.decision == "selected"

    # Invalid
    with pytest.raises(ValueError):
        FitScore(candidate_id="c1", decision="approved")


def test_selection_policy_allows_needs_review_but_never_rejected() -> None:
    policy_relaxed = SelectionPolicy(minimum_score=5.0, require_selected_decision=False)

    score_review = FitScore(candidate_id="rev", final_score=8.5, decision="needs_review")
    score_rejected = FitScore(candidate_id="rej", final_score=9.5, decision="rejected")

    # Relaxed policy allows selected and needs_review
    res = select_assignments({"slot_1": [score_review, score_rejected]}, policy=policy_relaxed)
    assert res.slots_filled == 1
    assert res.assignments["slot_1"].candidate_id == "rev"

    # Even with high score, rejected is never selected
    res_rejected = select_assignments({"slot_1": [score_rejected]}, policy=policy_relaxed)
    assert res_rejected.slots_filled == 0
    assert "slot_1" in res_rejected.unfilled_slots


def test_validate_intent_proof_with_relaxed_policy() -> None:
    brief = VisualBrief(
        article_title="Test",
        article_language="en",
        topic="test",
        image_slots=[{"slot_id": "slot_1", "target_heading": "H", "purpose": "p"}],
    )
    profile = PublisherProfile(profile_id="p1", brand_name="B", cms_type="wp", language="en")
    policy_relaxed = SelectionPolicy(require_selected_decision=False)

    candidates = [
        {
            "id": "c1",
            "provider": "local",
            "license": "cc0",
            "width": 1000,
            "height": 800,
            "local_path": "/tmp/a.jpg",
        }
    ]
    score_review = FitScore(candidate_id="c1", slot_id="slot_1", final_score=8.5, decision="needs_review")

    proof = compile_intent_proof(
        brief,
        profile,
        candidates,
        [(brief.image_slots[0], [score_review])],
        {"slot_1": score_review},
        selection_policy=policy_relaxed,
    )
    res = validate_intent_proof(proof)
    assert res["status"] == "passed"

    # If rejected candidate is assigned, intent validation must fail
    proof_corrupt = json.loads(json.dumps(proof))
    proof_corrupt["ledger"][0]["decision"] = "rejected"
    res_corrupt = validate_intent_proof(proof_corrupt)
    assert res_corrupt["status"] == "failed"
    assert any(e["code"] == "intent_assignment_decision_mismatch" for e in res_corrupt["errors"])


# ---------------------------------------------------------------------------
# 3. Decision Pack Review State Transitions
# ---------------------------------------------------------------------------
def test_transition_decision_pack_review_immutability_and_validation() -> None:
    pack = sample_decision_pack()
    assert pack["review"]["status"] == ReviewStatus.PENDING.value

    slot_id = pack["slots"][0]["slot_id"]
    decision = {
        "slot_id": slot_id,
        "action": ReviewAction.ACCEPT.value,
        "actor": "editor@example.com",
        "decided_at": "2026-11-08T12:00:00Z",
    }

    # Transition to reviewed (all slots covered)
    new_pack = transition_decision_pack_review(pack, [decision])
    assert new_pack["review"]["status"] == ReviewStatus.REVIEWED.value
    assert len(new_pack["review"]["decisions"]) == 1

    # Original pack must be untouched
    assert pack["review"]["status"] == ReviewStatus.PENDING.value
    assert len(pack["review"]["decisions"]) == 0

    # Explicit complete=False keeps it pending
    pending_pack = transition_decision_pack_review(pack, [decision], complete=False)
    assert pending_pack["review"]["status"] == ReviewStatus.PENDING.value

    # Reject invalid action
    bad_decision = dict(decision)
    bad_decision["action"] = "erase"
    with pytest.raises(ValueError, match="Transitioned decision pack is invalid"):
        transition_decision_pack_review(pack, [bad_decision])

    # Reject invalid input pack
    corrupt_pack = dict(pack)
    corrupt_pack["schema_version"] = "999"
    with pytest.raises(ValueError, match="Input decision pack is invalid"):
        transition_decision_pack_review(corrupt_pack, [decision])


# ---------------------------------------------------------------------------
# 4. PipelineRunner.publish and resolve_publish_status
# ---------------------------------------------------------------------------
def test_pipeline_runner_publish_states(tmp_path: Path) -> None:
    runner = PipelineRunner()

    plan_data = sample_visual_plan()
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan_data), encoding="utf-8")

    # Helper mock adapter
    mock_adapter = MagicMock()
    runner = PipelineRunner()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("pictovap.app.runtime.construct_plugin", lambda *args, **kwargs: mock_adapter)

        # dry-run
        res_dry = runner.publish(plan=str(plan_file), cms="mock", dry_run=True)
        assert res_dry["status"] == PublishStatus.READY.value
        assert res_dry["mode"] == PublishMode.DRY_RUN.value

        # Success (all completed)
        mock_adapter.place.return_value = {
            "status": "passed",
            "placed": [{"slot_id": "featured", "remote_id": 1}],
            "failed": [],
            "warnings": [],
        }
        res_completed = runner.publish(plan=str(plan_file), cms="mock")
        assert res_completed["status"] == PublishStatus.COMPLETED.value
        assert res_completed["mode"] == PublishMode.PUBLISH.value

        # Partial failure
        mock_adapter.place.return_value = {
            "status": "passed",
            "placed": [{"slot_id": "featured", "remote_id": 1}],
            "failed": [{"slot_id": "section_0", "error": "timeout"}],
            "warnings": [],
        }
        res_partial = runner.publish(plan=str(plan_file), cms="mock")
        assert res_partial["status"] == PublishStatus.PARTIAL.value

        # Complete failure
        mock_adapter.place.return_value = {
            "status": "failed",
            "placed": [],
            "failed": [{"slot_id": "featured", "error": "auth"}],
            "warnings": [],
        }
        res_failed = runner.publish(plan=str(plan_file), cms="mock")
        assert res_failed["status"] == PublishStatus.FAILED.value


def test_resolve_publish_status_helper() -> None:
    assert resolve_publish_status(dry_run=True, placed_count=0, failed_count=0) == "ready"
    assert resolve_publish_status(dry_run=False, placed_count=2, failed_count=0) == "completed"
    assert resolve_publish_status(dry_run=False, placed_count=1, failed_count=1) == "partial"
    assert resolve_publish_status(dry_run=False, placed_count=0, failed_count=2) == "failed"


def test_core_states_and_aggregation_helpers() -> None:
    # aggregate_check_status
    assert aggregate_check_status(["passed", "passed"]) == "passed"
    assert aggregate_check_status(["passed", "warning"]) == "warning"
    assert aggregate_check_status(["passed", "warning"], strict=True) == "failed"
    assert aggregate_check_status(["passed", "failed"]) == "failed"

    # guard_status_for_state
    assert guard_status_for_state("healthy") == "success"
    assert guard_status_for_state("empty") == "success"
    assert guard_status_for_state("drift") == "drift"
    assert guard_status_for_state("untracked") == "untracked"
    assert guard_status_for_state("healthy", failed=True) == "failed"
    assert guard_status_for_state("invalid") == "failed"

    # CandidateDecision eligibility
    assert CandidateDecision.SELECTED.is_eligible(require_selected=True) is True
    assert CandidateDecision.NEEDS_REVIEW.is_eligible(require_selected=True) is False
    assert CandidateDecision.NEEDS_REVIEW.is_eligible(require_selected=False) is True
    assert CandidateDecision.REJECTED.is_eligible(require_selected=False) is False

    # DoctorStatus & PlanDiffStatus
    assert DoctorStatus.READY.value == "ready"
    assert DoctorStatus.UNHEALTHY.value == "unhealthy"
    assert PlanDiffStatus.CHANGED.value == "changed"
    assert PlanDiffStatus.UNCHANGED.value == "unchanged"


# ---------------------------------------------------------------------------
# 5. guard_post_media status and state guarantees
# ---------------------------------------------------------------------------
def test_guard_post_media_returns_both_status_and_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WP_URL", "https://wp.example.com")
    monkeypatch.setenv("WP_USER", "admin")
    monkeypatch.setenv("WP_APP_PASSWORD", "secret")
    uploader = WordPressUploader(site="demo")

    # 1. Post context cannot be loaded
    monkeypatch.setattr(uploader, "fetch_post_context", lambda pid: None)
    res_no_post = uploader.guard_post_media(101)
    assert res_no_post["status"] == MediaGuardStatus.FAILED.value
    assert res_no_post["state"] == MediaIntegrityState.INVALID.value
    assert res_no_post["site"] == "demo"
    assert res_no_post["post_id"] == 101

    # 2. Untracked (no manifest)
    monkeypatch.setattr(uploader, "fetch_post_context", lambda pid: {"content_raw": "plain text"})
    monkeypatch.setattr("pictovap.services.wordpress.load_post_media_manifest", lambda site, pid: None)
    res_untracked = uploader.guard_post_media(101)
    assert res_untracked["status"] == MediaGuardStatus.UNTRACKED.value
    assert res_untracked["state"] == MediaIntegrityState.UNTRACKED.value

    # 3. Healthy
    dummy_manifest = {
        "site": "demo",
        "post_id": 101,
        "expected_media_ids": [42],
        "media_items": [{"media_id": 42}],
    }
    monkeypatch.setattr("pictovap.services.wordpress.load_post_media_manifest", lambda site, pid: dummy_manifest)
    monkeypatch.setattr(
        uploader,
        "fetch_post_context",
        lambda pid: {"content_raw": '<!-- wp:image {"id":42} --><img class="wp-image-42"/><!-- /wp:image -->'},
    )
    res_healthy = uploader.guard_post_media(101)
    assert res_healthy["status"] == MediaGuardStatus.SUCCESS.value
    assert res_healthy["state"] == MediaIntegrityState.HEALTHY.value

    # 4. Drift
    monkeypatch.setattr(uploader, "fetch_post_context", lambda pid: {"content_raw": "no images here"})
    res_drift = uploader.guard_post_media(101)
    assert res_drift["status"] == MediaGuardStatus.DRIFT.value
    assert res_drift["state"] == MediaIntegrityState.DRIFT.value

    # 5. Exception branch
    def _raise(*args: object, **kwargs: object) -> None:
        raise OSError("Disk failure")

    monkeypatch.setattr("pictovap.services.wordpress.load_post_media_manifest", _raise)
    res_err = uploader.guard_post_media(101)
    assert res_err["status"] == MediaGuardStatus.FAILED.value
    assert res_err["state"] == MediaIntegrityState.INVALID.value


# ---------------------------------------------------------------------------
# 6. VisualBrief.from_markdown fenced code blocks & H1 parsing
# ---------------------------------------------------------------------------
def test_visual_brief_markdown_fence_and_h1_isolation(tmp_path: Path) -> None:
    doc = """---
title: Original Article Title
---

# Top Level Header That Should Not Append To Previous

## First Section

Some introductory text.

```python
# A python comment heading
def foo():
    pass
```

~~~bash
# A bash comment heading
echo "hi"
~~~

# Disconnected Top Heading

## Second Section

More content for section 2.
"""
    path = tmp_path / "article.md"
    path.write_text(doc, encoding="utf-8")

    brief = VisualBrief.from_markdown(str(path))
    assert brief.article_title == "Original Article Title"

    # Only First Section and Second Section should be extracted as H2
    h2_sections = [s for s in brief.sections if s["level"] == "h2"]
    assert len(h2_sections) == 2
    assert h2_sections[0]["heading"] == "First Section"
    assert h2_sections[1]["heading"] == "Second Section"

    # Ensure python/bash comments inside fences were not extracted as headings
    headings = [s["heading"] for s in brief.sections]
    assert "A python comment heading" not in headings
    assert "A bash comment heading" not in headings
    assert "Disconnected Top Heading" not in headings

    # Excerpt of First Section must not include the subsequent Disconnected Top Heading
    first_slot = next(s for s in brief.image_slots if s["slot_id"] == "section_0")
    assert "Disconnected Top Heading" not in first_slot["section_excerpt"]


# ---------------------------------------------------------------------------
# 7. Environment reloading & reset_project_env
# ---------------------------------------------------------------------------
def test_load_project_env_reloads_when_workspace_dir_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws1.mkdir()
    ws2.mkdir()

    (ws1 / ".env").write_text("PICTOVAP_TEST_VAR=ws1_value\n", encoding="utf-8")
    (ws2 / ".env").write_text("PICTOVAP_TEST_VAR=ws2_value\n", encoding="utf-8")

    reset_project_env()
    monkeypatch.setenv("PICTOVAP_WORKSPACE_DIR", str(ws1))
    monkeypatch.delenv("PICTOVAP_TEST_VAR", raising=False)

    load_project_env()
    import os

    assert os.environ.get("PICTOVAP_TEST_VAR") == "ws1_value"

    # Switch workspace directory and reload
    monkeypatch.setenv("PICTOVAP_WORKSPACE_DIR", str(ws2))
    monkeypatch.delenv("PICTOVAP_TEST_VAR", raising=False)

    load_project_env()
    assert os.environ.get("PICTOVAP_TEST_VAR") == "ws2_value"

    # Test reset_project_env
    reset_project_env()
    monkeypatch.setenv("PICTOVAP_TEST_VAR", "manual_override")
    load_project_env()
    assert os.environ.get("PICTOVAP_TEST_VAR") == "manual_override"
