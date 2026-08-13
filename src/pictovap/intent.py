"""Visual Intent Compiler and proof-carrying plan records.

This module turns the existing visual brief and deterministic fit scores into
an explicit editorial intent graph plus a decision ledger. It does not call
providers, use an LLM, or change candidate selection; it makes the decisions
and their evidence inspectable for editors and third-party integrations.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from pictovap.core.primitives import FitScore, VisualBrief
from pictovap.core.profile import PublisherProfile


INTENT_SCHEMA_VERSION = "1"
_STOP_WORDS = frozenset({"the", "and", "for", "with", "from", "this", "that", "into", "after"})


@dataclass(frozen=True)
class IntentConstraint:
    """One hard or soft condition applied to an editorial image decision."""

    code: str
    kind: str
    requirement: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "kind": self.kind, "requirement": self.requirement}


@dataclass(frozen=True)
class VisualIntentSlot:
    """The visual job a selected image must perform in one article slot."""

    slot_id: str
    role: str
    target_heading: str
    purpose: str
    query_terms: tuple[str, ...]
    constraints: tuple[IntentConstraint, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "role": self.role,
            "target_heading": self.target_heading,
            "purpose": self.purpose,
            "query_terms": list(self.query_terms),
            "constraints": [constraint.to_dict() for constraint in self.constraints],
        }


@dataclass(frozen=True)
class VisualIntentGraph:
    """A deterministic graph of article-level visual intent."""

    article_id: str
    article_title: str
    language: str
    topic: str
    publisher_profile: str
    slots: tuple[VisualIntentSlot, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": INTENT_SCHEMA_VERSION,
            "compiler": "pictovap.visual-intent",
            "article_id": self.article_id,
            "article_title": self.article_title,
            "language": self.language,
            "topic": self.topic,
            "publisher_profile": self.publisher_profile,
            "slots": [slot.to_dict() for slot in self.slots],
        }


def _terms(*values: str) -> tuple[str, ...]:
    words: list[str] = []
    seen: set[str] = set()
    for value in values:
        for word in re.findall(r"[\w'-]+", value.lower()):
            if len(word) < 3 or word in _STOP_WORDS or word in seen:
                continue
            seen.add(word)
            words.append(word)
    return tuple(words[:12])


def build_visual_intent_graph(brief: VisualBrief, profile: PublisherProfile) -> VisualIntentGraph:
    """Compile a VisualBrief into a stable, explainable intent graph."""
    constraints = (
        IntentConstraint("license_declared", "hard", "candidate declares a usable license"),
        IntentConstraint("source_reference", "hard", "candidate exposes a local path or source URL"),
        IntentConstraint("minimum_dimensions", "hard", "candidate is at least 800x600 pixels"),
        IntentConstraint("semantic_alignment", "soft", "candidate keywords align with the slot context"),
        IntentConstraint("technical_headroom", "soft", "candidate meets the preferred 1200x800 dimensions"),
        IntentConstraint("cms_suitability", "soft", "candidate fits the target placement role"),
        IntentConstraint("global_diversity", "soft", "candidate does not create avoidable repetition"),
    )
    slots = tuple(
        VisualIntentSlot(
            slot_id=str(raw_slot.get("slot_id", "")),
            role="featured" if raw_slot.get("slot_id") == "featured" else "inline",
            target_heading=str(raw_slot.get("target_heading", "")),
            purpose=str(raw_slot.get("purpose", "")),
            query_terms=_terms(
                brief.topic,
                brief.article_title,
                str(raw_slot.get("target_heading", "")),
                str(raw_slot.get("section_excerpt", "")),
            ),
            constraints=constraints,
        )
        for raw_slot in brief.image_slots
    )
    return VisualIntentGraph(
        article_id=str(brief.article_id or ""),
        article_title=brief.article_title,
        language=brief.article_language,
        topic=brief.topic,
        publisher_profile=profile.profile_id,
        slots=slots,
    )


def _check(code: str, passed: bool, observed: Any, requirement: str) -> dict[str, Any]:
    return {"code": code, "status": "passed" if passed else "failed", "observed": observed, "requirement": requirement}


def _candidate_evidence(candidate: Mapping[str, Any], score: FitScore) -> dict[str, Any]:
    return {
        "provider": candidate.get("provider"),
        "license": candidate.get("license"),
        "width": candidate.get("width"),
        "height": candidate.get("height"),
        "source_reference": bool(candidate.get("local_path") or candidate.get("source_url")),
        "score": score.final_score,
    }


def build_decision_ledger(
    graph: VisualIntentGraph,
    candidates: Iterable[Mapping[str, Any]],
    scored_slots: Iterable[tuple[Mapping[str, Any], Iterable[FitScore]]],
    assignments: Mapping[str, FitScore],
) -> list[dict[str, Any]]:
    """Create one reasoned ledger entry for every candidate-slot evaluation."""
    candidate_map = {str(candidate.get("id")): candidate for candidate in candidates}
    ledger: list[dict[str, Any]] = []
    for raw_slot, scores in scored_slots:
        slot_id = str(raw_slot.get("slot_id", ""))
        assigned = assignments.get(slot_id)
        for score in scores:
            candidate = candidate_map.get(score.candidate_id, {})
            license_value = str(candidate.get("license") or "").strip().lower()
            width = candidate.get("width", 0)
            height = candidate.get("height", 0)
            hard_checks = [
                _check(
                    "license_declared",
                    license_value not in {"", "unknown", "none"},
                    candidate.get("license"),
                    "non-empty license",
                ),
                _check(
                    "source_reference",
                    bool(candidate.get("local_path") or candidate.get("source_url")),
                    bool(candidate.get("local_path") or candidate.get("source_url")),
                    "local_path or source_url",
                ),
                _check(
                    "minimum_dimensions",
                    isinstance(width, int) and isinstance(height, int) and width >= 800 and height >= 600,
                    f"{width}x{height}",
                    "at least 800x600",
                ),
            ]
            soft_checks = [
                _check(
                    "semantic_alignment",
                    score.contextual_relevance + score.section_relevance >= 1.0,
                    round(score.contextual_relevance + score.section_relevance, 2),
                    "contextual + section relevance >= 1.0",
                ),
                _check(
                    "technical_headroom",
                    score.technical_quality >= 3.0,
                    score.technical_quality,
                    "preferred technical quality",
                ),
                _check(
                    "cms_suitability",
                    score.cms_suitability >= 1.5,
                    score.cms_suitability,
                    "CMS suitability >= 1.5",
                ),
                _check(
                    "global_diversity",
                    score.duplication_risk <= 0.0,
                    score.duplication_risk,
                    "duplication risk <= 0",
                ),
            ]
            hard_failures = [check["code"] for check in hard_checks if check["status"] == "failed"]
            reason_codes = list(hard_failures)
            is_assigned = assigned is not None and assigned.candidate_id == score.candidate_id
            if is_assigned:
                reason_codes.append("assigned_by_global_policy")
            elif score.decision == "rejected":
                reason_codes.append("rejected_by_fit_policy")
            else:
                reason_codes.append("not_selected_by_global_policy")
            ledger.append({
                "slot_id": slot_id,
                "candidate_id": score.candidate_id,
                "decision": score.decision,
                "assignment": "assigned" if is_assigned else "not_assigned",
                "reason_codes": reason_codes,
                "human_reason": score.human_reason,
                "hard_constraints": hard_checks,
                "soft_constraints": soft_checks,
                "evidence": _candidate_evidence(candidate, score),
            })
    return ledger


def compile_intent_proof(
    brief: VisualBrief,
    profile: PublisherProfile,
    candidates: Iterable[Mapping[str, Any]],
    scored_slots: Iterable[tuple[Mapping[str, Any], Iterable[FitScore]]],
    assignments: Mapping[str, FitScore],
) -> dict[str, Any]:
    """Compile the graph and decision ledger into a proof-carrying plan block."""
    graph = build_visual_intent_graph(brief, profile)
    ledger = build_decision_ledger(graph, candidates, scored_slots, assignments)
    selected = sum(entry["assignment"] == "assigned" for entry in ledger)
    hard_failures = sum(
        any(check["status"] == "failed" for check in entry["hard_constraints"])
        for entry in ledger
    )
    return {
        "schema_version": INTENT_SCHEMA_VERSION,
        "status": "passed" if hard_failures == 0 else "warning",
        "graph": graph.to_dict(),
        "ledger": ledger,
        "summary": {
            "slots": len(graph.slots),
            "evaluations": len(ledger),
            "selected": selected,
            "hard_constraint_failures": hard_failures,
        },
    }


def render_intent_markdown(proof: Mapping[str, Any]) -> str:
    """Render a decision ledger for human editorial review."""
    graph = proof.get("graph", {})
    summary = proof.get("summary", {})
    lines = [
        "# Visual Intent Explanation",
        "",
        f"**Article:** {graph.get('article_title', '')}  ",
        f"**Status:** `{proof.get('status', 'unknown')}`  ",
        f"**Slots:** {summary.get('slots', 0)}  ",
        f"**Evaluations:** {summary.get('evaluations', 0)}  ",
        f"**Selected:** {summary.get('selected', 0)}",
        "",
        "| Slot | Candidate | Score decision | Assignment | Reasons |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in proof.get("ledger", []):
        reasons = ", ".join(f"`{reason}`" for reason in entry.get("reason_codes", []))
        lines.append(
            f"| `{entry.get('slot_id', '')}` | `{entry.get('candidate_id', '')}` | "
            f"`{entry.get('decision', '')}` | `{entry.get('assignment', '')}` | {reasons} |"
        )
    lines.extend(["", "Every decision includes hard constraints, soft constraints, and candidate evidence.", ""])
    return "\n".join(lines)


def intent_proof_to_json(proof: Mapping[str, Any]) -> str:
    """Serialize an intent proof with stable formatting."""
    return json.dumps(proof, ensure_ascii=False, indent=2) + "\n"


__all__ = [
    "INTENT_SCHEMA_VERSION",
    "IntentConstraint",
    "VisualIntentGraph",
    "VisualIntentSlot",
    "build_decision_ledger",
    "build_visual_intent_graph",
    "compile_intent_proof",
    "intent_proof_to_json",
    "render_intent_markdown",
]
