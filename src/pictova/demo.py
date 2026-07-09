#!/usr/bin/env python3
"""
Pictovap Local Demo
-------------------
Runs the full visual finishing pipeline with no external credentials.

Usage:
    python -m pictova.demo
    python examples/demo.py
    make demo
"""

import json
import hashlib
import sys
import argparse
from pathlib import Path

# Add src to path when run directly from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pictova.core.primitives import (
    VisualBrief,
    FitScore,
    ProvenancePack,
    CMSPlacement,
    PlacementInstruction,
)
from pictova.core.profile import PublisherProfile


# ---------------------------------------------------------------------------
# Mock image candidates (no external APIs, no credentials)
# ---------------------------------------------------------------------------
MOCK_CANDIDATES = [
    {
        "id": "img-backpack-01",
        "filename": "minimal-backpack.jpg",
        "provider": "local",
        "source_type": "local",
        "local_path": "examples/assets/minimal-backpack.jpg",
        "license": "CC0",
        "attribution": None,
        "keywords": ["backpack", "travel", "minimalist", "packing"],
        "width": 1920,
        "height": 1280,
    },
    {
        "id": "img-forest-02",
        "filename": "forest-path.jpg",
        "provider": "local",
        "source_type": "local",
        "local_path": "examples/assets/forest-path.jpg",
        "license": "CC0",
        "attribution": None,
        "keywords": ["forest", "nature", "path", "serenity", "trees"],
        "width": 1600,
        "height": 1067,
    },
    {
        "id": "img-generic-03",
        "filename": "generic-stock.jpg",
        "provider": "stock",
        "source_type": "api",
        "local_path": None,
        "source_url": "https://example.com/generic-stock.jpg",
        "license": "editorial",
        "attribution": "Example Stock Co.",
        "keywords": ["map", "tourist", "generic"],
        "width": 800,
        "height": 600,
    },
    {
        "id": "img-lowres-04",
        "filename": "blurry-phone.jpg",
        "provider": "local",
        "source_type": "local",
        "local_path": "examples/assets/blurry-phone.jpg",
        "license": "owned",
        "attribution": None,
        "keywords": ["phone", "blurry", "travel"],
        "width": 320,
        "height": 240,
    },
    {
        "id": "img-sunset-05",
        "filename": "sunset-mountains.jpg",
        "provider": "unsplash_mock",
        "source_type": "api",
        "local_path": None,
        "source_url": "https://unsplash.com/photos/mock-sunset",
        "license": "unsplash",
        "attribution": "Photo by Jane Doe on Unsplash",
        "keywords": ["sunset", "mountains", "nature", "travel", "landscape"],
        "width": 2400,
        "height": 1600,
    },
]


# ---------------------------------------------------------------------------
# Deterministic scoring (rule-based, not ML)
# ---------------------------------------------------------------------------
def score_candidate(candidate: dict, slot: dict, brief: VisualBrief) -> FitScore:
    """Score a candidate image against a slot using deterministic rules."""
    slot_id = slot.get("slot_id", "")
    slot_purpose = slot.get("purpose", "")
    target_heading = slot.get("target_heading", "")

    # Contextual relevance: keyword overlap with article topic + title
    topic_words = set((brief.topic + " " + brief.article_title).lower().split())
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

    # Duplication risk: simple stub (always 0 in demo)
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

    # Decision
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


def generate_markdown_report(output: dict) -> str:
    """Generate a human-readable Markdown report from the JSON output."""
    lines = []
    
    brief = output.get("visual_brief", {})
    profile = output.get("profile", {})
    scores = output.get("fit_scores", {})
    packs = output.get("provenance_packs", [])
    placement = output.get("cms_placement", {})
    
    lines.append("# Pictovap Visual Plan")
    lines.append("")
    
    lines.append("## Article")
    lines.append(f"- **Title:** {brief.get('article_title', 'Unknown')}")
    lines.append(f"- **Language:** {brief.get('article_language', 'en')}")
    source_path = output.get("source_path", "Unknown")
    lines.append(f"- **Source path:** {source_path}")
    lines.append(f"- **Publisher profile:** {profile.get('brand', 'Unknown')} ({profile.get('id', 'unknown')})")
    lines.append("")
    
    lines.append("## Visual Brief")
    lines.append(f"- **Detected sections:** {len(brief.get('sections', []))}")
    lines.append(f"- **Required image slots:** {len(brief.get('image_slots', []))}")
    for slot in brief.get('image_slots', []):
        lines.append(f"- **Preferred image type per slot ({slot['slot_id']}):** {slot['preferred_type']}")
        if slot.get('section_excerpt'):
            lines.append(f"- **Section excerpt/context if available ({slot['slot_id']}):** {slot['section_excerpt']}")
    lines.append("")
    
    lines.append("## Selected Images")
    for pack in packs:
        slot_id = pack['slot_id']
        lines.append("For each selected image:")
        lines.append(f"- **slot:** {slot_id}")
        lines.append(f"- **target section:** {pack.get('placement_target', 'top')}")
        lines.append(f"- **candidate ID:** {pack['image_id']}")
        
        # Find score and reason
        final_score = "Unknown"
        reason = "Unknown"
        for s in scores.get(slot_id, []):
            if s['candidate_id'] == pack['image_id']:
                final_score = str(s['final_score'])
                reason = s['human_reason']
                break
                
        lines.append(f"- **final score:** {final_score}")
        lines.append(f"- **reason:** {reason}")
        lines.append(f"- **alt text:** {pack['generated_alt_text']}")
        lines.append(f"- **caption:** {pack['generated_caption']}")
        lines.append("")

    lines.append("## Candidates Requiring Review")
    has_review = False
    for slot_id, slot_scores in scores.items():
        for s in slot_scores:
            if s['decision'] in ('needs_review', 'rejected'):
                has_review = True
                lines.append(f"- **candidate ID:** {s['candidate_id']}")
                lines.append(f"- **slot:** {slot_id}")
                lines.append(f"- **reason:** {s['human_reason']}")
                lines.append(f"- **score:** {s['final_score']}")
                lines.append("")
            
    if not has_review:
        lines.append("No candidates flagged for manual review.")
        lines.append("")
        
    lines.append("## Provenance")
    for pack in packs:
        lines.append(f"- **source type:** {pack.get('source_type', 'local')}")
        lines.append(f"- **provider:** {pack['provider']}")
        lines.append(f"- **source URL/local path:** {pack.get('source_url') or pack.get('local_source_path')}")
        lines.append(f"- **license status:** {pack['license_status']}")
        lines.append(f"- **attribution:** {pack.get('attribution', 'None')}")
        lines.append(f"- **content hash:** {pack['content_hash']}")
        lines.append("")

    lines.append("## CMS Placement Plan")
    for instr in placement.get("placements", []):
        lines.append(f"- **target section:** {instr['target_section'] or 'top'}")
        lines.append(f"- **placement strategy:** {instr['placement_strategy']}")
        lines.append(f"- **image role:** {instr['image_role']}")
        lines.append(f"- **output path:** {instr['output_path']}")
        lines.append("")
    
    lines.append("## Editorial Review Checklist")
    lines.append("- Verify selected images fit the article context")
    lines.append("- Verify license/attribution before publishing")
    lines.append("- Review alt text and captions")
    lines.append("- Confirm CMS placement before live publishing")
    
    return "\n".join(lines)

def generate_report_from_file(plan_path: str, output_path: str):
    import sys
    plan_file = Path(plan_path)
    if not plan_file.exists():
        print(f"Error: Plan file not found at {plan_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(plan_file, "r") as f:
        output = json.load(f)
        
    report = generate_markdown_report(output)
    
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")
    print(f"Report written to {output_path}")


# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------
def run_demo(article_path_str: str = None, profile_path_str: str = None, output_path_str: str = None, report_path_str: str = None):
    """Run the full Pictovap demo pipeline."""
    print("=" * 60)
    print("  Pictovap Local Demo")
    print("  Visual finishing pipeline — no credentials required")
    print("=" * 60)

    # 1. Load publisher profile
    if profile_path_str:
        profile_path = Path(profile_path_str)
        if not profile_path.exists():
            print(f"Error: Profile not found at {profile_path_str}", file=sys.stderr)
            sys.exit(1)
        profile = PublisherProfile.from_yaml(str(profile_path))
    else:
        profile = PublisherProfile.get_default_profile()
    
    print(f"\n[Profile] Loaded: {profile.brand_name} ({profile.profile_id})")

    # 2. Parse article into Visual Brief
    if article_path_str:
        article_path = Path(article_path_str)
        if not article_path.exists():
            print(f"Error: Article not found at {article_path_str}", file=sys.stderr)
            sys.exit(1)
    else:
        article_path = Path(__file__).parent / "sample-article.md"
        if not article_path.exists():
            article_path = Path(__file__).resolve().parent.parent.parent / "examples" / "sample-article.md"
            if not article_path.exists():
                 print(f"Error: Default sample article not found.")
                 sys.exit(1)

    brief = VisualBrief.from_markdown(str(article_path), fallback_lang=profile.language if profile else "en")
    brief.topic = "minimalist travel"
    brief.detected_location = None
    
    # Override only if language_mode is override
    if profile and getattr(profile, "language_mode", "fallback") == "override" and profile.language:
        brief.article_language = profile.language
        
    brief.article_id = "demo-article-001"

    print(f"\n[1/4] Visual Brief")
    print(f"  Title:    {brief.article_title}")
    print(f"  Sections: {len(brief.sections)}")
    print(f"  Slots:    {len(brief.image_slots)}")
    for slot in brief.image_slots:
        excerpt = slot.get('section_excerpt', '')
        excerpt_disp = f" (Context: {excerpt[:40]}...)" if len(excerpt) > 40 else (f" (Context: {excerpt})" if excerpt else "")
        print(f"    - {slot['slot_id']}: {slot['purpose']} ({slot['preferred_type']}){excerpt_disp}")

    # 3. Score all candidates for each slot
    print(f"\n[2/4] Fit Scores ({len(MOCK_CANDIDATES)} candidates x {len(brief.image_slots)} slots)")
    all_scores = []
    for slot in brief.image_slots:
        slot_scores = []
        for cand in MOCK_CANDIDATES:
            score = score_candidate(cand, slot, brief)
            slot_scores.append(score)
        slot_scores.sort(key=lambda s: s.final_score, reverse=True)
        all_scores.append((slot, slot_scores))

        best = slot_scores[0]
        print(f"  Slot '{slot['slot_id']}':")
        for s in slot_scores:
            icon = "v" if s.decision == "selected" else ("x" if s.decision == "rejected" else "?")
            print(f"    {icon} {s.candidate_id}: {s.final_score:.1f} ({s.decision}) -- {s.human_reason}")

    # 4. Select best candidate per slot & build Provenance Packs
    print(f"\n[3/4] Provenance Packs")
    packs = []
    selected_map = {}  # slot_id -> candidate
    used_ids = set()

    for slot, slot_scores in all_scores:
        for score in slot_scores:
            if score.decision == "selected" and score.candidate_id not in used_ids:
                cand = next(c for c in MOCK_CANDIDATES if c["id"] == score.candidate_id)
                used_ids.add(score.candidate_id)
                selected_map[slot["slot_id"]] = cand

                content = f"{cand['id']}:{cand['filename']}"
                chash = hashlib.sha256(content.encode()).hexdigest()[:16]
                gen_name = f"pictovap_{cand['filename'].rsplit('.', 1)[0]}.webp"

                from pictova.core.metadata import generate_local_alt_text, generate_local_caption
                alt_text = generate_local_alt_text(cand, slot, language=brief.article_language)
                caption = generate_local_caption(cand, slot, language=brief.article_language)

                pack = ProvenancePack(
                    image_id=cand["id"],
                    source_type=cand.get("source_type", "local"),
                    provider=cand.get("provider", "local"),
                    source_url=cand.get("source_url"),
                    local_source_path=cand.get("local_path"),
                    license_status=cand.get("license", "unknown"),
                    attribution=cand.get("attribution"),
                    original_filename=cand["filename"],
                    generated_filename=gen_name,
                    content_hash=chash,
                    article_id=brief.article_id,
                    slot_id=slot["slot_id"],
                    placement_target=slot.get("purpose", ""),
                    generated_alt_text=alt_text,
                    generated_caption=caption,
                    processing_actions=["resize_1200", "webp_convert", "exif_strip"],
                )
                packs.append(pack)
                print(f"  {pack.slot_id}: {pack.original_filename} -> {pack.generated_filename}")
                print(f"    Provider: {pack.provider}, License: {pack.license_status}, Hash: {pack.content_hash}")
                break

    # 5. Build CMS Placement plan
    print(f"\n[4/4] CMS Placement Plan")
    instructions = []
    for pack in packs:
        slot = next((s for s in brief.image_slots if s["slot_id"] == pack.slot_id), {})
        instr = PlacementInstruction(
            slot_id=pack.slot_id,
            output_path=pack.generated_filename,
            target_section=slot.get("target_heading", ""),
            placement_strategy="featured" if pack.slot_id == "featured" else "after_heading",
            image_role="featured" if pack.slot_id == "featured" else "content",
            alt_text=pack.generated_alt_text,
            caption=pack.generated_caption,
        )
        instructions.append(instr)
        print(f"  [{instr.image_role}] {instr.output_path} -> {instr.placement_strategy}:{instr.target_section or 'top'}")

    placement = CMSPlacement(
        article_id=brief.article_id,
        adapter_target="mock_adapter",
        target_platform="demo",
        placements=instructions,
    )

    # 6. Assemble full output
    output = {
        "pipeline": "Pictovap Visual Finishing Demo",
        "visual_brief": brief.to_dict(),
        "fit_scores": {
            slot["slot_id"]: [s.to_dict() for s in scores]
            for slot, scores in all_scores
        },
        "provenance_packs": [p.to_dict() for p in packs],
        "cms_placement": placement.to_dict(),
        "source_path": str(article_path),
        "profile": {
            "id": profile.profile_id,
            "brand": profile.brand_name,
            "cms_type": profile.cms_type,
            "language": profile.language,
        },
    }

    # 7. Write output file
    if output_path_str:
        out_path = Path(output_path_str)
    else:
        out_path = Path(__file__).parent / "sample-output.json"
        if not out_path.parent.exists() or out_path.parent.name == "pictova":
            out_path = Path(__file__).resolve().parent.parent.parent / "examples" / "sample-output.json"
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # 8. Write Markdown report if requested
    if report_path_str:
        report_path = Path(report_path_str)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_markdown = generate_markdown_report(output)
        report_path.write_text(report_markdown, encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"  Output written to: {out_path}")
    if report_path_str:
        print(f"  Report written to: {report_path}")
    print(f"  Brief:      {len(brief.image_slots)} slots from {len(brief.sections)} sections")
    print(f"  Evaluated:  {len(MOCK_CANDIDATES)} candidates")
    print(f"  Selected:   {len(packs)} images")
    print(f"  Rejected:   {sum(1 for _, ss in all_scores for s in ss if s.decision == 'rejected')} candidates")
    print(f"  Placements: {len(placement.placements)} instructions")
    print(f"{'=' * 60}")
    print("  Demo completed. No credentials were used.")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pictovap Local Demo")
    parser.add_argument("--article", help="Path to a custom Markdown article", default=None)
    parser.add_argument("--profile", help="Path to a custom Publisher Profile YAML", default=None)
    parser.add_argument("--output", help="Path to write the JSON output", default=None)
    parser.add_argument("--report", nargs='?', const="examples/sample-report.md", help="Path to write the human-readable Markdown report", default=None)
    args = parser.parse_args()

    run_demo(
        article_path_str=args.article,
        profile_path_str=args.profile,
        output_path_str=args.output,
        report_path_str=args.report
    )
