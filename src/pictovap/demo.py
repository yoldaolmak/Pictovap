#!/usr/bin/env python3
"""
Pictovap Local Demo
-------------------
Runs the full visual finishing pipeline with no external credentials.

The demo owns no planning logic. It supplies deterministic fixture candidates,
calls the planning engine, and renders the returned plan for a terminal — so
what a contributor reads on screen is always the artifact, never a parallel
narration of it.

Usage:
    python -m pictovap.demo
    make demo
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pictovap.core.profile import PublisherProfile
from pictovap.data.demo_candidates import MOCK_CANDIDATES
from pictovap.engine.planner import build_visual_plan
from pictovap.engine.reporting import write_plan_artifacts


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
    1. The repo-relative ``examples/articles/travel-guide.md``. This is the file
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


# ---------------------------------------------------------------------------
# Terminal rendering — a pure function of the plan artifact
# ---------------------------------------------------------------------------
def render_plan_console(plan: dict[str, Any]) -> str:
    """Render the pipeline walkthrough a contributor sees, entirely from the plan."""
    brief = plan.get("visual_brief", {})
    scores = plan.get("fit_scores", {})
    slots = brief.get("image_slots", [])
    lines: list[str] = []

    lines.append("")
    lines.append("[1/4] Visual Brief")
    lines.append(f"  Title:    {brief.get('article_title', '')}")
    lines.append(f"  Sections: {len(brief.get('sections', []))}")
    lines.append(f"  Slots:    {len(slots)}")
    for slot in slots:
        excerpt = slot.get("section_excerpt", "")
        if len(excerpt) > 40:
            context = f" (Context: {excerpt[:40]}...)"
        elif excerpt:
            context = f" (Context: {excerpt})"
        else:
            context = ""
        lines.append(
            f"    - {slot['slot_id']}: {slot['purpose']} ({slot['preferred_type']}){context}"
        )

    evaluated = plan.get("candidates_evaluated", 0)
    lines.append("")
    lines.append(f"[2/4] Fit Scores ({evaluated} candidates x {len(slots)} slots)")
    for slot in slots:
        slot_id = slot["slot_id"]
        lines.append(f"  Slot '{slot_id}':")
        for score in scores.get(slot_id, []):
            decision = score.get("decision")
            icon = "v" if decision == "selected" else ("x" if decision == "rejected" else "?")
            lines.append(
                f"    {icon} {score['candidate_id']}: {score['final_score']:.1f} "
                f"({decision}) -- {score['human_reason']}"
            )

    lines.append("")
    lines.append("[3/4] Provenance Packs")
    for warning in plan.get("planning_diagnostics", {}).get("warnings", []):
        lines.append(f"  Warning: {warning}")
    for pack in plan.get("provenance_packs", []):
        lines.append(f"  {pack['slot_id']}: {pack['original_filename']} -> {pack['generated_filename']}")
        lines.append(
            f"    Provider: {pack['provider']}, License: {pack['license_status']}, "
            f"Hash: {pack['content_hash']}"
        )

    lines.append("")
    lines.append("[4/4] CMS Placement Plan")
    for instruction in plan.get("cms_placement", {}).get("placements", []):
        lines.append(
            f"  [{instruction['image_role']}] {instruction['output_path']} -> "
            f"{instruction['placement_strategy']}:{instruction['target_section'] or 'top'}"
        )

    return "\n".join(lines)


def render_plan_summary(plan: dict[str, Any]) -> str:
    """Render the closing counts an editor uses to sanity-check a run."""
    brief = plan.get("visual_brief", {})
    rejected = sum(
        1
        for slot_scores in plan.get("fit_scores", {}).values()
        for score in slot_scores
        if score.get("decision") == "rejected"
    )
    return "\n".join([
        f"  Brief:      {len(brief.get('image_slots', []))} slots from "
        f"{len(brief.get('sections', []))} sections",
        f"  Evaluated:  {plan.get('candidates_evaluated', 0)} candidates",
        f"  Selected:   {len(plan.get('provenance_packs', []))} images",
        f"  Rejected:   {rejected} candidates",
        f"  Placements: {len(plan.get('cms_placement', {}).get('placements', []))} instructions",
    ])


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------
def run_demo(
    article_path_str: str | None = None,
    profile_path_str: str | None = None,
    output_path_str: str | None = None,
    report_path_str: str | None = None,
) -> None:
    """Run the credential-free demo from the CLI.

    This is the terminal-facing wrapper: it exits with code 1 on bad input and
    always writes the JSON plan (and optionally a Markdown report) to disk.
    Library callers should use `pictovap.api.create_visual_plan()` instead.
    """
    print("=" * 60)
    print("  Pictovap Local Demo")
    print("  Visual finishing pipeline — no credentials required")
    print("=" * 60)

    if profile_path_str:
        profile_path = Path(profile_path_str)
        if not profile_path.exists():
            print(f"Error: Profile not found at {profile_path_str}", file=sys.stderr)
            sys.exit(1)
        profile = PublisherProfile.from_yaml(str(profile_path))
    else:
        profile = PublisherProfile.get_default_profile()

    print(f"\n[Profile] Loaded: {profile.brand_name} ({profile.profile_id})")

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

    plan = build_visual_plan(
        article_path,
        profile,
        use_real_sources=False,
        source_label=None if article_path_str else "sample-article.md",
        fallback_candidates=MOCK_CANDIDATES,
        fallback_mode="demo",
    )
    print(render_plan_console(plan))
    out_path = write_plan_artifacts(plan, output_path_str, report_path_str)

    print(f"\n{'=' * 60}")
    print(f"  Output written to: {out_path}")
    if report_path_str:
        print(f"  Report written to: {report_path_str}")
    print(render_plan_summary(plan))
    print(f"{'=' * 60}")
    print("  Demo completed. No credentials were used.")
    print()


__all__ = ["MOCK_CANDIDATES", "render_plan_console", "render_plan_summary", "run_demo"]


if __name__ == "__main__":
    # `--report` with no value (a bare flag) should still resolve to a real,
    # writable path in the caller's workspace, alongside the JSON output.
    _bare_report_default = str(Path.cwd() / "sample-report.md")

    parser = argparse.ArgumentParser(description="Pictovap Local Demo")
    parser.add_argument("--article", help="Path to a custom Markdown article", default=None)
    parser.add_argument("--profile", help="Path to a custom Publisher Profile YAML", default=None)
    parser.add_argument("--output", help="Path to write the JSON output", default=None)
    parser.add_argument("--report", nargs='?', const=_bare_report_default,
                        help="Path to write the human-readable Markdown report", default=None)
    args = parser.parse_args()

    if args.article:
        # A real article was given: use the same real-adapter-aware path as
        # `pictovap plan`, not the always-fixture demo path.
        from pictovap import api

        plan = api.create_visual_plan(
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
