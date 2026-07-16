#!/usr/bin/env python3
"""
Pictovap Local Demo
-------------------
Runs the full visual finishing pipeline with no external credentials.

Usage:
    python -m pictovap.demo
    python examples/demo.py
    make demo
"""

from __future__ import annotations

import json
import hashlib
import sys
import argparse
from pathlib import Path

# Add src to path when run directly from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pictovap.core.primitives import (  # noqa: E402
    VisualBrief,
    FitScore,
    ProvenancePack,
    CMSPlacement,
    PlacementInstruction,
)
from pictovap.core.profile import PublisherProfile  # noqa: E402
from pictovap.core.sources import fetch_candidates  # noqa: E402
from pictovap.testing.contracts import assert_image_source_contract  # noqa: E402


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


def _is_dev_install() -> bool:
    """Check if we're running in a dev/source-tree context vs. a real installed package.

    Returns True if repo-relative examples/ directory exists (indicating a source checkout
    with pip install -e . or direct repo clone), False for a real PyPI install.
    """
    repo_examples = Path(__file__).resolve().parent.parent.parent / "examples"
    return repo_examples.exists() and repo_examples.is_dir()


def _resolve_sample_article() -> Path | None:
    """Locate the credential-free demo's default sample article.

    Preference order:
    1. The repo-relative ``examples/sample-article.md``. This is the file
       contributors actually edit when iterating on the example in a source
       checkout (plain clone or ``pip install -e .``); preferring it means
       their edits are picked up immediately, with no reinstall/resync step.
    2. The packaged copy at ``pictovap/data/sample-article.md``, shipped as
       real package data (see ``[tool.setuptools.package-data]`` in
       pyproject.toml). This is what makes ``pictovap demo`` work for a
       genuine ``pip install pictovap`` from PyPI: ``examples/`` is a
       top-level repo directory that is never installed alongside the
       package, so it doesn't exist relative to site-packages — only the
       packaged copy does.

    Returns None if neither is found (should not happen for a correctly
    packaged install).
    """
    repo_relative = Path(__file__).resolve().parent.parent.parent / "examples" / "sample-article.md"
    if repo_relative.exists():
        return repo_relative

    try:
        import importlib.resources as resources
        packaged = resources.files("pictovap.data").joinpath("sample-article.md")
        if packaged.is_file():
            return Path(str(packaged))
    except (ModuleNotFoundError, FileNotFoundError, TypeError):
        pass

    return None


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
# Core pipeline (shared by the CLI runner and the public library API)
# ---------------------------------------------------------------------------
def _build_plan_output(
    article_path: Path,
    profile: PublisherProfile,
    *,
    use_real_sources: bool,
    source_label: str | None = None,
    provider_adapter: object | None = None,
    provider_name: str | None = None,
) -> dict:
    """Run the visual finishing pipeline for an already-resolved article path
    and profile, and return the JSON-shaped plan output.

    This is the one place the pipeline logic lives — `run_demo()` (CLI) and
    `create_visual_plan()` (library API) both call this after doing their
    own input validation.

    `use_real_sources` controls whether configured image source adapters
    (local/unsplash/deposit) are actually queried. `run_demo()` always
    passes False: the demo's whole point is to be a deterministic,
    credential-free example, so it must not vary based on whatever
    credentials happen to be present in the environment/.env.
    """
    brief = VisualBrief.from_markdown(str(article_path), fallback_lang=profile.language if profile else "en")
    serialized_source = source_label or str(article_path)
    brief.source_path = serialized_source
    brief.topic = "minimalist travel"
    brief.detected_location = None

    # Override only if language_mode is override
    if profile and getattr(profile, "language_mode", "fallback") == "override" and profile.language:
        brief.article_language = profile.language

    brief.article_id = "demo-article-001"

    print("\n[1/4] Visual Brief")
    print(f"  Title:    {brief.article_title}")
    print(f"  Sections: {len(brief.sections)}")
    print(f"  Slots:    {len(brief.image_slots)}")
    for slot in brief.image_slots:
        excerpt = slot.get('section_excerpt', '')
        excerpt_disp = f" (Context: {excerpt[:40]}...)" if len(
            excerpt) > 40 else (f" (Context: {excerpt})" if excerpt else "")
        print(f"    - {slot['slot_id']}: {slot['purpose']} ({slot['preferred_type']}){excerpt_disp}")

    # 2b. Fetch real candidates from the profile's configured image sources,
    # falling back to deterministic mock candidates when none are
    # configured/credentialed (or when running the credential-free demo).
    candidates = []
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
    if not candidates and not explicit_provider:
        candidates = MOCK_CANDIDATES
        provider_mode = "demo-fallback" if use_real_sources else "demo"

    # 3. Score all candidates for each slot
    print(f"\n[2/4] Fit Scores ({len(candidates)} candidates x {len(brief.image_slots)} slots)")
    all_scores = []
    for slot in brief.image_slots:
        slot_scores = []
        for cand in candidates:
            score = score_candidate(cand, slot, brief)
            slot_scores.append(score)
        slot_scores.sort(key=lambda s: s.final_score, reverse=True)
        all_scores.append((slot, slot_scores))

        print(f"  Slot '{slot['slot_id']}':")
        for s in slot_scores:
            icon = "v" if s.decision == "selected" else ("x" if s.decision == "rejected" else "?")
            print(f"    {icon} {s.candidate_id}: {s.final_score:.1f} ({s.decision}) -- {s.human_reason}")

    # 4. Select best candidate per slot & build Provenance Packs
    print("\n[3/4] Provenance Packs")
    packs = []
    selected_map = {}  # slot_id -> candidate
    used_ids = set()

    for slot, slot_scores in all_scores:
        for score in slot_scores:
            if score.decision == "selected" and score.candidate_id not in used_ids:
                cand = next(c for c in candidates if c["id"] == score.candidate_id)
                used_ids.add(score.candidate_id)
                selected_map[slot["slot_id"]] = cand

                content = f"{cand['id']}:{cand['filename']}"
                chash = hashlib.sha256(content.encode()).hexdigest()[:16]
                gen_name = f"pictovap_{cand['filename'].rsplit('.', 1)[0]}.webp"

                from pictovap.core.demo_metadata import generate_local_alt_text, generate_local_caption
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
    print("\n[4/4] CMS Placement Plan")
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
        print(
            f"  [{instr.image_role}] {instr.output_path} -> "
            f"{instr.placement_strategy}:{instr.target_section or 'top'}"
        )

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
        "source_path": serialized_source,
        "candidates_evaluated": len(candidates),
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
    return output


def _write_plan_files(output: dict, output_path_str: str | None, report_path_str: str | None) -> Path:
    """Write the JSON plan (and optional Markdown report) to disk. Returns the JSON path used."""
    if output_path_str:
        out_path = Path(output_path_str)
    else:
        # Detect context: dev/source tree vs. real installed package
        if _is_dev_install():
            # Dev context: write to repo-relative examples/ directory (preserves existing test expectations)
            out_path = Path(__file__).resolve().parent.parent.parent / "examples" / "sample-output.json"
        else:
            # Real install: write to current working directory where user can reliably find it
            out_path = Path.cwd() / "sample-output.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    # Only write a report when the caller actually asked for one (an explicit
    # path, or the CLI's `--report` bare-flag default resolved upstream in
    # __main__). No implicit/unconditional report on every demo run.
    if report_path_str:
        report_path = Path(report_path_str)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(generate_markdown_report(output), encoding="utf-8")

    return out_path


# ---------------------------------------------------------------------------
# Public library API
# ---------------------------------------------------------------------------
def create_visual_plan(
    article: str,
    profile: str | None = None,
    *,
    output: str | None = None,
    report: str | None = None,
    provider_adapter: object | None = None,
    provider_name: str | None = None,
) -> dict:
    """Build a visual plan for an article — the library equivalent of
    `pictovap plan`. Importable and usable without going through the CLI.

    Args:
        article: Path to a Markdown article.
        profile: Path to a Publisher Profile YAML. Uses the default demo
            profile when omitted.
        output: If given, also writes the JSON plan to this path.
        report: If given, also writes a Markdown editor report to this path.
        provider_adapter: An already constructed third-party image-source
            adapter. When supplied, its candidates are validated and no demo
            fallback is used.
        provider_name: Entry-point name recorded in runtime metadata when a
            third-party provider is supplied.

    Returns:
        The JSON-shaped visual plan as a dict (visual_brief, fit_scores,
        provenance_packs, cms_placement, ...).

    Raises:
        FileNotFoundError: if `article` or `profile` doesn't exist.

    Example:
        from pictova import create_visual_plan

        plan = create_visual_plan(
            article="article.md",
            profile="publisher.yaml",
        )
    """
    article_path = Path(article)
    if not article_path.exists():
        raise FileNotFoundError(f"Article not found: {article}")

    if profile:
        profile_path = Path(profile)
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {profile}")
        pub_profile = PublisherProfile.from_yaml(str(profile_path))
    else:
        pub_profile = PublisherProfile.get_default_profile()

    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        plan_output = _build_plan_output(
            article_path,
            pub_profile,
            use_real_sources=True,
            provider_adapter=provider_adapter,
            provider_name=provider_name,
        )

    if output or report:
        _write_plan_files(plan_output, output, report)

    return plan_output


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------
def run_demo(
    article_path_str: str | None = None,
    profile_path_str: str | None = None,
    output_path_str: str | None = None,
    report_path_str: str | None = None,
) -> None:
    """Run the full Pictovap demo pipeline from the CLI.

    This is the terminal-facing wrapper: it prints progress, exits with
    code 1 on bad input, and always writes the JSON plan (and optionally a
    Markdown report) to disk. Library callers should use
    `create_visual_plan()` instead.
    """
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

    # 2. Resolve article path
    if article_path_str:
        article_path = Path(article_path_str)
        if not article_path.exists():
            print(f"Error: Article not found at {article_path_str}", file=sys.stderr)
            sys.exit(1)
    else:
        article_path = _resolve_sample_article()
        if article_path is None:
            print("Error: Default sample article not found.")
            sys.exit(1)

    source_label = None if article_path_str else "sample-article.md"
    output = _build_plan_output(
        article_path,
        profile,
        use_real_sources=False,
        source_label=source_label,
    )
    out_path = _write_plan_files(output, output_path_str, report_path_str)

    print(f"\n{'=' * 60}")
    print(f"  Output written to: {out_path}")
    if report_path_str:
        print(f"  Report written to: {report_path_str}")
    brief = output["visual_brief"]
    rejected = sum(
        1 for scores in output["fit_scores"].values() for s in scores if s["decision"] == "rejected"
    )
    print(f"  Brief:      {len(brief['image_slots'])} slots from {len(brief['sections'])} sections")
    print(f"  Evaluated:  {output['candidates_evaluated']} candidates")
    print(f"  Selected:   {len(output['provenance_packs'])} images")
    print(f"  Rejected:   {rejected} candidates")
    print(f"  Placements: {len(output['cms_placement']['placements'])} instructions")
    print(f"{'=' * 60}")
    print("  Demo completed. No credentials were used.")
    print()


if __name__ == "__main__":
    # `--report` with no value (a bare flag) should still resolve to a real,
    # writable path -- consistent with where _write_plan_files() puts the
    # JSON output: examples/ in a dev/source checkout, cwd for a real install.
    _bare_report_default = (
        "examples/sample-report.md" if _is_dev_install() else str(Path.cwd() / "sample-report.md")
    )

    parser = argparse.ArgumentParser(description="Pictovap Local Demo")
    parser.add_argument("--article", help="Path to a custom Markdown article", default=None)
    parser.add_argument("--profile", help="Path to a custom Publisher Profile YAML", default=None)
    parser.add_argument("--output", help="Path to write the JSON output", default=None)
    parser.add_argument("--report", nargs='?', const=_bare_report_default,
                        help="Path to write the human-readable Markdown report", default=None)
    args = parser.parse_args()

    if args.article:
        # A real article was given: use the same real-adapter-aware path as
        # `pictovap plan`, not the always-mock demo path.
        plan = create_visual_plan(
            article=args.article,
            profile=args.profile,
            output=args.output,
            report=args.report,
        )
        print(json.dumps(plan, ensure_ascii=False, indent=2) if not args.output else f"Plan written to {args.output}")
    else:
        run_demo(
            article_path_str=None,
            profile_path_str=args.profile,
            output_path_str=args.output,
            report_path_str=args.report,
        )
