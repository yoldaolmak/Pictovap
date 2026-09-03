"""The visual planning engine: article and profile in, visual plan out.

This module is the single place the planning pipeline lives. It is silent and
side-effect-free by contract: it prints nothing, writes no files, and returns
the JSON-shaped visual plan. Every progress line a human sees is rendered from
the returned plan, so a terminal view can never diverge from the artifact.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

from pictovap.core.demo_metadata import generate_local_alt_text, generate_local_caption
from pictovap.core.primitives import (
    CMSPlacement,
    PlacementInstruction,
    ProvenancePack,
    VisualBrief,
)
from pictovap.core.profile import PublisherProfile
from pictovap.core.selection import select_assignments
from pictovap.core.sources import fetch_candidates
from pictovap.core.visual_similarity import collect_candidate_fingerprints
from pictovap.engine.scoring import score_candidate
from pictovap.intent import compile_intent_proof
from pictovap.testing.contracts import assert_image_source_contract


PLAN_LABEL = "Pictovap Visual Plan"


def build_visual_plan(
    article_path: Path | None,
    profile: PublisherProfile,
    *,
    use_real_sources: bool,
    source_label: str | None = None,
    provider_adapter: object | None = None,
    provider_name: str | None = None,
    brief: VisualBrief | None = None,
    fallback_candidates: Sequence[Mapping[str, Any]] | None = None,
    fallback_mode: str = "fallback",
) -> dict[str, Any]:
    """Run the visual finishing pipeline and return the JSON-shaped plan.

    `use_real_sources` controls whether the profile's configured image source
    adapters are queried at all. `fallback_candidates` is the caller's policy
    for an empty candidate pool: the engine holds no fixture of its own, so a
    caller that supplies none gets an honestly empty plan instead of silently
    borrowing example data.
    """
    if brief is None:
        if article_path is None:
            raise ValueError("An article path or VisualBrief is required")
        brief = VisualBrief.from_markdown(
            str(article_path), fallback_lang=profile.language if profile else "en"
        )
    serialized_source = source_label or brief.source_path or str(article_path or "article")
    brief.source_path = serialized_source
    brief.topic = brief.topic or brief.article_title

    if profile and getattr(profile, "language_mode", "fallback") == "override" and profile.language:
        brief.article_language = profile.language

    brief.article_id = brief.article_id or "demo-article-001"

    # 1. Collect candidates from an explicit plugin, the profile's configured
    #    sources, or the caller's fallback pool — in that order.
    candidates: list[dict[str, Any]] = []
    explicit_provider = provider_adapter is not None
    provider_mode = "plugin" if explicit_provider else "profile"
    if explicit_provider:
        candidates = assert_image_source_contract(
            provider_adapter,
            query=brief.topic or brief.article_title,
            count=8,
        )
    elif use_real_sources and profile:
        candidates = fetch_candidates(profile, query=brief.topic or brief.article_title, count=8)
    if not candidates and not explicit_provider and fallback_candidates:
        candidates = [dict(candidate) for candidate in fallback_candidates]
        provider_mode = fallback_mode

    # 2. Score every candidate against every slot.
    all_scores = []
    for slot in brief.image_slots:
        slot_scores = [score_candidate(candidate, slot, brief) for candidate in candidates]
        slot_scores.sort(key=lambda score: score.final_score, reverse=True)
        all_scores.append((slot, slot_scores))

    # 3. Assign candidates globally, then build a Provenance Pack per assignment.
    #    Global selection prevents a strong candidate from being silently reused
    #    when a different eligible image can cover another editorial slot.
    score_map = {slot["slot_id"]: scores for slot, scores in all_scores}
    candidate_fingerprints = collect_candidate_fingerprints(candidates)
    selection = select_assignments(score_map, candidate_fingerprints=candidate_fingerprints)

    packs = []
    for slot, _slot_scores in all_scores:
        score = selection.assignments.get(slot["slot_id"])
        if score is None:
            continue
        candidate = next(item for item in candidates if item["id"] == score.candidate_id)
        content = f"{candidate['id']}:{candidate['filename']}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        generated_filename = f"pictovap_{candidate['filename'].rsplit('.', 1)[0]}.webp"
        packs.append(ProvenancePack(
            image_id=candidate["id"],
            source_type=candidate.get("source_type", "local"),
            provider=candidate.get("provider", "local"),
            source_url=candidate.get("source_url"),
            local_source_path=candidate.get("local_path"),
            license_status=candidate.get("license", "unknown"),
            attribution=candidate.get("attribution"),
            original_filename=candidate["filename"],
            generated_filename=generated_filename,
            content_hash=content_hash,
            article_id=brief.article_id,
            slot_id=slot["slot_id"],
            placement_target=slot.get("purpose", ""),
            generated_alt_text=generate_local_alt_text(
                candidate, slot, language=brief.article_language
            ),
            generated_caption=generate_local_caption(
                candidate, slot, language=brief.article_language
            ),
            processing_actions=["resize_1200", "webp_convert", "exif_strip"],
        ))

    # 4. Turn each pack into one CMS-neutral placement instruction.
    instructions = []
    for pack in packs:
        slot = next((item for item in brief.image_slots if item["slot_id"] == pack.slot_id), {})
        instructions.append(PlacementInstruction(
            slot_id=pack.slot_id,
            output_path=pack.generated_filename,
            target_section=slot.get("target_heading", ""),
            placement_strategy="featured" if pack.slot_id == "featured" else "after_heading",
            image_role="featured" if pack.slot_id == "featured" else "content",
            alt_text=pack.generated_alt_text,
            caption=pack.generated_caption,
        ))

    placement = CMSPlacement(
        article_id=brief.article_id,
        adapter_target="mock_adapter",
        target_platform="demo",
        placements=instructions,
    )

    intent_proof = compile_intent_proof(
        brief,
        profile,
        candidates,
        all_scores,
        selection.assignments,
    )

    return {
        "pipeline": PLAN_LABEL,
        "visual_brief": brief.to_dict(),
        "fit_scores": {
            slot["slot_id"]: [score.to_dict() for score in scores]
            for slot, scores in all_scores
        },
        "provenance_packs": [pack.to_dict() for pack in packs],
        "cms_placement": placement.to_dict(),
        "source_path": serialized_source,
        "candidates_evaluated": len(candidates),
        "planning_diagnostics": selection.to_dict(),
        "intent_proof": intent_proof,
        "profile": {
            "id": profile.profile_id,
            "brand": profile.brand_name,
            "cms_type": profile.cms_type,
            "language": profile.language,
        },
        "runtime": {
            "provider": {
                "mode": provider_mode,
                "name": provider_name if explicit_provider else None,
            },
        },
    }


__all__ = ["PLAN_LABEL", "build_visual_plan"]
