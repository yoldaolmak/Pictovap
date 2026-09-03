"""Human- and machine-facing renderings of a Pictovap visual plan.

Every renderer here is a pure function of the plan artifact. Nothing in this
module re-derives a planning decision, so a report can never disagree with the
plan it was rendered from.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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
    frontmatter = brief.get("frontmatter", {})
    if frontmatter:
        lines.append("- **Frontmatter context:**")
        for key in sorted(frontmatter):
            value = json.dumps(frontmatter[key], ensure_ascii=False, sort_keys=True)
            lines.append(f"  - **{key}:** {value}")
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


def write_plan_artifacts(
    plan: dict[str, Any],
    output_path_str: str | None,
    report_path_str: str | None,
    report_renderer: object | None = None,
) -> Path:
    """Write the JSON plan (and optional Markdown report). Returns the JSON path used."""
    if output_path_str:
        out_path = Path(output_path_str)
    else:
        # Artifacts belong to the caller's workspace. Writing into the source
        # checkout would mutate a tracked example; writing into an installed
        # package could fail because site-packages is read-only.
        out_path = Path.cwd() / "sample-output.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    # Only write a report when the caller actually asked for one. No implicit
    # report on every run.
    if report_path_str:
        report = render_report(plan, report_renderer)
        report_path = Path(report_path_str)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")

    return out_path


def render_report(plan: dict[str, Any], renderer: object | None = None) -> str:
    """Render a plan with the built-in Markdown report or an installed renderer."""
    if renderer is None:
        return generate_markdown_report(plan)
    from pictovap.testing.contracts import assert_report_renderer_contract

    return assert_report_renderer_contract(renderer, plan=plan)


def generate_report_from_file(
    plan_path: str,
    output_path: str,
    renderer: object | None = None,
) -> Path:
    """Render a stored plan file into an editor report. Raises on unreadable input."""
    plan_file = Path(plan_path)
    if not plan_file.exists():
        raise FileNotFoundError(f"Plan file not found at {plan_path}")

    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(render_report(plan, renderer), encoding="utf-8")
    return out_file


__all__ = [
    "generate_markdown_report",
    "generate_report_from_file",
    "render_report",
    "write_plan_artifacts",
]
