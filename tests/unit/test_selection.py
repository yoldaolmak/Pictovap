"""Tests for the global, constraint-aware image assignment engine."""

from pictovap.core.primitives import FitScore
from pictovap.core.selection import SelectionPolicy, select_assignments


def _score(slot_id: str, candidate_id: str, value: float) -> FitScore:
    return FitScore(
        candidate_id=candidate_id,
        slot_id=slot_id,
        final_score=value,
        decision="selected" if value >= 8 else "needs_review",
    )


def test_global_assignment_beats_greedy_duplicate_choice():
    result = select_assignments({
        "featured": [_score("featured", "hero", 10), _score("featured", "detail", 9)],
        "section_0": [_score("section_0", "hero", 10), _score("section_0", "detail", 8)],
    })

    assert result.assignments["featured"].candidate_id == "detail"
    assert result.assignments["section_0"].candidate_id == "hero"
    assert result.total_score == 19
    assert result.coverage_ratio == 1.0


def test_assignment_reports_unfilled_slots_and_capacity_warning():
    result = select_assignments({
        "featured": [_score("featured", "hero", 10)],
        "section_0": [_score("section_0", "hero", 10)],
    })

    assert result.slots_filled == 1
    assert result.unfilled_slots == ("section_0",)
    assert result.coverage_ratio == 0.5
    assert result.warnings


def test_policy_can_allow_reuse_for_small_pools():
    result = select_assignments(
        {
            "featured": [_score("featured", "hero", 10)],
            "section_0": [_score("section_0", "hero", 9)],
        },
        policy=SelectionPolicy(allow_candidate_reuse=True),
    )

    assert result.slots_filled == 2
    assert result.assignments["featured"].candidate_id == "hero"
    assert result.assignments["section_0"].candidate_id == "hero"


def test_below_threshold_candidates_require_review():
    result = select_assignments({"featured": [_score("featured", "hero", 7.9)]})

    assert result.slots_filled == 0
    assert result.unfilled_slots == ("featured",)
