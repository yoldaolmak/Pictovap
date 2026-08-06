"""Deterministic, constraint-aware image assignment for visual plans.

The planner scores every candidate independently, but selection is a global
decision: one image should not silently occupy several editorial slots when
another viable image exists.  This module keeps that policy explicit and
serializable so adapters can reason about the same contract as the built-in
pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Mapping

from pictovap.core.visual_similarity import visual_similarity


@dataclass(frozen=True)
class SelectionPolicy:
    """Rules applied after candidate scoring and before provenance creation."""

    minimum_score: float = 8.0
    allow_candidate_reuse: bool = False
    require_selected_decision: bool = True
    similarity_threshold: float = 0.92
    similarity_penalty: float = 2.0


@dataclass(frozen=True)
class SelectionResult:
    """Global assignment outcome with enough detail for an editor or adapter."""

    assignments: Mapping[str, Any]
    total_score: float
    slots_requested: int
    slots_filled: int
    unfilled_slots: tuple[str, ...]
    policy: SelectionPolicy
    warnings: tuple[str, ...] = ()
    diversity_penalty: float = 0.0
    similarity_pairs: tuple[Mapping[str, Any], ...] = ()

    @property
    def coverage_ratio(self) -> float:
        if self.slots_requested == 0:
            return 1.0
        return round(self.slots_filled / self.slots_requested, 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm": "deterministic_maximum_weight_assignment",
            "policy": {
                "minimum_score": self.policy.minimum_score,
                "allow_candidate_reuse": self.policy.allow_candidate_reuse,
                "require_selected_decision": self.policy.require_selected_decision,
                "similarity_threshold": self.policy.similarity_threshold,
                "similarity_penalty": self.policy.similarity_penalty,
            },
            "slots_requested": self.slots_requested,
            "slots_filled": self.slots_filled,
            "coverage_ratio": self.coverage_ratio,
            "total_score": round(self.total_score, 2),
            "adjusted_total_score": round(self.total_score - self.diversity_penalty, 2),
            "diversity_penalty": round(self.diversity_penalty, 2),
            "similarity_pairs": [dict(pair) for pair in self.similarity_pairs],
            "unfilled_slots": list(self.unfilled_slots),
            "warnings": list(self.warnings),
        }


def _eligible(score: Any, policy: SelectionPolicy) -> bool:
    if score.final_score < policy.minimum_score:
        return False
    return not policy.require_selected_decision or score.decision == "selected"


def _pair_penalty(
    candidate_id: str,
    used_mask: int,
    candidate_ids: list[str],
    fingerprints: Mapping[str, str],
    policy: SelectionPolicy,
) -> float:
    """Calculate the marginal penalty for adding a visually similar image."""
    fingerprint = fingerprints.get(candidate_id)
    if not fingerprint or policy.similarity_penalty <= 0:
        return 0.0
    penalty = 0.0
    for index, used_id in enumerate(candidate_ids):
        if not (used_mask & (1 << index)):
            continue
        similarity = visual_similarity(fingerprint, fingerprints.get(used_id))
        if similarity >= policy.similarity_threshold:
            scale = (similarity - policy.similarity_threshold) / max(
                1.0 - policy.similarity_threshold, 0.0001
            )
            penalty += policy.similarity_penalty * scale
    return round(penalty, 4)


def _selected_similarity_pairs(
    selected_ids: list[str],
    fingerprints: Mapping[str, str],
    policy: SelectionPolicy,
) -> tuple[Mapping[str, Any], ...]:
    pairs: list[Mapping[str, Any]] = []
    for index, left_id in enumerate(selected_ids):
        for right_id in selected_ids[index + 1:]:
            similarity = visual_similarity(fingerprints.get(left_id), fingerprints.get(right_id))
            if similarity >= policy.similarity_threshold:
                scale = (similarity - policy.similarity_threshold) / max(
                    1.0 - policy.similarity_threshold, 0.0001
                )
                pairs.append({
                    "left_candidate_id": left_id,
                    "right_candidate_id": right_id,
                    "similarity": similarity,
                    "penalty": round(policy.similarity_penalty * scale, 4),
                })
    return tuple(pairs)


def select_assignments(
    scores_by_slot: Mapping[str, list[Any]],
    *,
    policy: SelectionPolicy | None = None,
    candidate_fingerprints: Mapping[str, str] | None = None,
) -> SelectionResult:
    """Choose a globally optimal, non-conflicting candidate for each slot.

    The dynamic-programming solver is exact for the normal adapter contract
    (up to 20 distinct candidates).  Larger result sets use a deterministic
    scarcity-first fallback, keeping runtime bounded for unusually large
    external providers without adding a dependency.
    """
    policy = policy or SelectionPolicy()
    fingerprints = candidate_fingerprints or {}
    slot_ids = list(scores_by_slot)
    eligible: dict[str, list[Any]] = {
        slot_id: sorted(
            (score for score in scores if _eligible(score, policy)),
            key=lambda score: (-score.final_score, score.candidate_id),
        )
        for slot_id, scores in scores_by_slot.items()
    }
    candidate_ids = sorted({score.candidate_id for scores in eligible.values() for score in scores})
    assignments: dict[str, Any] = {}

    if policy.allow_candidate_reuse:
        assignments = {slot_id: scores[0] for slot_id, scores in eligible.items() if scores}
    elif len(candidate_ids) <= 20:
        candidate_index = {candidate_id: index for index, candidate_id in enumerate(candidate_ids)}

        @lru_cache(maxsize=None)
        def solve(index: int, used_mask: int) -> tuple[float, int, tuple[tuple[str, str], ...], float, float]:
            if index == len(slot_ids):
                return 0.0, 0, (), 0.0, 0.0
            slot_id = slot_ids[index]
            best = solve(index + 1, used_mask)
            for score in eligible[slot_id]:
                bit = 1 << candidate_index[score.candidate_id]
                if used_mask & bit:
                    continue
                pair_penalty = _pair_penalty(
                    score.candidate_id, used_mask, candidate_ids, fingerprints, policy
                )
                tail_score, tail_count, tail_assignments, tail_raw, tail_penalty = solve(
                    index + 1, used_mask | bit
                )
                candidate = (
                    tail_score + score.final_score - pair_penalty,
                    tail_count + 1,
                    ((slot_id, score.candidate_id),) + tail_assignments,
                    tail_raw + score.final_score,
                    tail_penalty + pair_penalty,
                )
                if (
                    candidate[0] > best[0]
                    or (candidate[0] == best[0] and candidate[1] > best[1])
                    or (
                        candidate[0] == best[0]
                        and candidate[1] == best[1]
                        and candidate[2] < best[2]
                    )
                ):
                    best = candidate
            return best

        _, _, chosen, _, _ = solve(0, 0)
        chosen_ids = dict(chosen)
        assignments = {
            slot_id: next(score for score in eligible[slot_id] if score.candidate_id == candidate_id)
            for slot_id, candidate_id in chosen_ids.items()
        }
    else:
        # External providers may return very large candidate sets.  Preserve
        # bounded runtime while still prioritising constrained editorial slots.
        used: set[str] = set()
        for slot_id, scores in sorted(eligible.items(), key=lambda item: (len(item[1]), item[0])):
            selected = max(
                (
                    score for score in scores
                    if score.candidate_id not in used
                ),
                key=lambda score: (
                    score.final_score - _pair_penalty(
                        score.candidate_id,
                        sum(1 << candidate_ids.index(item) for item in used),
                        candidate_ids,
                        fingerprints,
                        policy,
                    ),
                    score.final_score,
                    score.candidate_id,
                ),
                default=None,
            )
            if selected is not None:
                assignments[slot_id] = selected
                used.add(selected.candidate_id)

    unfilled = tuple(slot_id for slot_id in slot_ids if slot_id not in assignments)
    warnings = []
    if unfilled:
        warnings.append(f"{len(unfilled)} editorial slot(s) have no eligible unique candidate")
    if not policy.allow_candidate_reuse and len(candidate_ids) < len(slot_ids):
        warnings.append("Candidate pool is smaller than the requested slot count")
    similarity_pairs = _selected_similarity_pairs(
        [score.candidate_id for score in assignments.values()], fingerprints, policy
    )
    diversity_penalty = round(sum(float(pair["penalty"]) for pair in similarity_pairs), 4)
    if diversity_penalty:
        warnings.append("Selected images include visually similar candidates; review variety before publishing")
    return SelectionResult(
        assignments=assignments,
        total_score=sum(score.final_score for score in assignments.values()),
        slots_requested=len(slot_ids),
        slots_filled=len(assignments),
        unfilled_slots=unfilled,
        policy=policy,
        warnings=tuple(warnings),
        diversity_penalty=diversity_penalty,
        similarity_pairs=similarity_pairs,
    )


__all__ = ["SelectionPolicy", "SelectionResult", "select_assignments"]
