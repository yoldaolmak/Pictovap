"""Deterministic Fit Score evaluation of one candidate against one slot.

Scoring is rule-based, not learned: every component is reproducible from the
candidate metadata and the slot context, and every decision carries the
human-readable reason that produced it.
"""

from __future__ import annotations

from typing import Any

from pictovap.core.primitives import FitScore, VisualBrief, _metadata_text


def score_candidate(candidate: dict[str, Any], slot: dict[str, Any], brief: VisualBrief) -> FitScore:
    """Score a candidate image against a slot using deterministic rules."""
    slot_id = slot.get("slot_id", "")
    slot_purpose = slot.get("purpose", "")
    target_heading = slot.get("target_heading", "")

    # Contextual relevance: keyword overlap with article context and metadata
    metadata_context = _metadata_text(
        brief.frontmatter,
        "keywords", "tags", "categories", "category", "audience", "location",
    )
    topic_words = set((brief.topic + " " + brief.article_title + " " + metadata_context).lower().split())
    kw = set(k.lower() for k in candidate.get("keywords", []))
    overlap = len(topic_words & kw)
    contextual = min(overlap / max(len(topic_words), 1) * 5.0, 5.0)

    # Section relevance: keyword overlap with target heading and context
    section_excerpt = slot.get("section_excerpt", "")
    section_text = f"{target_heading} {section_excerpt}".strip()
    section_words = set(section_text.lower().split()) if section_text else set()
    section_overlap = len(section_words & kw)
    section_rel = min(section_overlap / max(len(section_words), 1) * 3.0, 3.0) if section_words else 1.5

    # Technical quality: based on resolution
    w = candidate.get("width", 0)
    h = candidate.get("height", 0)
    if w >= 1200 and h >= 800:
        tech = 3.0
    elif w >= 800 and h >= 600:
        tech = 2.0
    else:
        tech = 0.5

    # Duplication risk: reserved for cross-article duplicate policy
    dup_risk = 0.0

    # Source trust
    provider = candidate.get("provider", "")
    trust_map = {"local": 2.0, "unsplash_mock": 1.5, "stock": 1.0}
    source_trust = trust_map.get(provider, 1.0)

    # License confidence
    lic = candidate.get("license", "unknown")
    lic_map = {"CC0": 2.0, "owned": 2.0, "unsplash": 1.5, "editorial": 0.5, "unknown": 0.0}
    license_conf = lic_map.get(lic, 0.5)

    # CMS suitability: landscape preferred for featured
    if slot_purpose == "featured_image":
        cms_suit = 2.0 if w > h else 1.0
    else:
        cms_suit = 1.5

    final = contextual + section_rel + tech + source_trust + license_conf + cms_suit - dup_risk

    if tech < 1.0:
        decision = "rejected"
        reason = f"Resolution too low ({w}x{h})"
    elif license_conf < 0.5:
        decision = "rejected"
        reason = f"License status unclear ({lic})"
    elif final >= 8.0:
        decision = "selected"
        reason = f"Strong fit: contextual={contextual:.1f}, quality={tech:.1f}, license={license_conf:.1f}"
    else:
        decision = "needs_review"
        reason = f"Moderate fit (score={final:.1f}), manual review recommended"

    return FitScore(
        candidate_id=candidate["id"],
        slot_id=slot_id,
        contextual_relevance=round(contextual, 2),
        section_relevance=round(section_rel, 2),
        technical_quality=tech,
        duplication_risk=dup_risk,
        source_trust=source_trust,
        license_confidence=license_conf,
        cms_suitability=cms_suit,
        final_score=round(final, 2),
        decision=decision,
        human_reason=reason,
    )


__all__ = ["score_candidate"]
