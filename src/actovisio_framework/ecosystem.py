"""Ecosystem integration helpers for adjacent publishing tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


SUPPORTED_TOOL_KINDS = (
    "markdown-to-wordpress",
    "ai-draft",
    "media-uploader",
    "gutenberg-tool",
    "cms-automation",
    "static-site-migration",
)


@dataclass(frozen=True)
class EcosystemPattern:
    """Describes how Pictovap fits beside an adjacent publishing tool."""

    tool_kind: str
    label: str
    owned_by_tool: str
    pictovap_role: str
    boundary: str
    readme_heading: str
    readme_intro: str


PATTERNS: Dict[str, EcosystemPattern] = {
    "markdown-to-wordpress": EcosystemPattern(
        tool_kind="markdown-to-wordpress",
        label="Markdown-to-WordPress importer",
        owned_by_tool="Markdown conversion, WordPress authentication, post creation, and import/publish transport.",
        pictovap_role=(
            "Pre-publish image planning: visual brief, candidate scoring, provenance, "
            "alt/caption review, and CMS placement plan."
        ),
        boundary="Run Pictovap before the importer; keep the importer responsible for the final WordPress write.",
        readme_heading="Optional image planning workflow",
        readme_intro=(
            "{project} handles Markdown-to-WordPress import. If the editorial workflow "
            "also needs image selection, attribution, alt/caption review, or Gutenberg "
            "placement planning before import, add a separate pre-publish image planning step."
        ),
    ),
    "ai-draft": EcosystemPattern(
        tool_kind="ai-draft",
        label="AI draft tool",
        owned_by_tool="Draft generation, source expansion, editing UI, and WordPress draft creation.",
        pictovap_role=(
            "Post-draft visual finishing: section-level image intent, candidate evaluation, "
            "license provenance, editor report, and placement instructions."
        ),
        boundary="Run Pictovap after a draft exists and before the editor approves media for publishing.",
        readme_heading="Optional image workflow",
        readme_intro=(
            "{project} creates review-ready drafts. Image sourcing, license provenance, "
            "alt/caption review, and Gutenberg image placement can remain a separate "
            "editorial workflow after the draft is available."
        ),
    ),
    "media-uploader": EcosystemPattern(
        tool_kind="media-uploader",
        label="Media upload script",
        owned_by_tool="Uploading already chosen local media and replacing article references with CMS URLs.",
        pictovap_role=(
            "Before-upload planning: decide which image belongs where, record source and "
            "license data, and prepare editor-approved metadata."
        ),
        boundary="Use Pictovap before upload; use the uploader only after media choices are approved.",
        readme_heading="Pre-upload image planning",
        readme_intro=(
            "{project} uploads media that is already referenced or selected. If editors "
            "need to decide which images belong under each heading before upload, use a "
            "separate image planning step first."
        ),
    ),
    "gutenberg-tool": EcosystemPattern(
        tool_kind="gutenberg-tool",
        label="Gutenberg block tool",
        owned_by_tool="Rendering, validating, or modifying Gutenberg block markup.",
        pictovap_role=(
            "Placement intent and review data: target heading, image role, alt text, "
            "caption, source, license, and attribution."
        ),
        boundary="Use Pictovap to decide placement intent; let the Gutenberg tool own block execution.",
        readme_heading="Image placement planning",
        readme_intro=(
            "{project} works at the Gutenberg block boundary. If the workflow needs a "
            "reviewable decision about where images belong before blocks are written, "
            "Pictovap can provide that placement plan."
        ),
    ),
    "cms-automation": EcosystemPattern(
        tool_kind="cms-automation",
        label="CMS automation tool",
        owned_by_tool="CMS-specific transport, authentication, field mapping, scheduling, or publishing.",
        pictovap_role=(
            "CMS-neutral visual plan and editor report before a CMS-specific automation writes anything."
        ),
        boundary="Keep Pictovap as the reviewable planning layer before the CMS automation step.",
        readme_heading="Visual planning before CMS automation",
        readme_intro=(
            "{project} owns CMS automation. Pictovap can sit before that step when editors "
            "need image selection, provenance, alt/caption review, and placement intent."
        ),
    ),
    "static-site-migration": EcosystemPattern(
        tool_kind="static-site-migration",
        label="Static-site migration tool",
        owned_by_tool="Reading Markdown or generated HTML and moving content into another publishing target.",
        pictovap_role=(
            "Migration-time visual review: inspect article sections, plan images, "
            "and preserve provenance before import."
        ),
        boundary="Run Pictovap before migration import so visual decisions are not buried in the transport step.",
        readme_heading="Image planning before migration",
        readme_intro=(
            "{project} moves prepared content into a publishing target. Pictovap can add "
            "a reviewable image plan before the migration writes to a CMS."
        ),
    ),
}


def normalize_tool_kind(tool_kind: str) -> str:
    """Return a supported ecosystem tool kind or raise ValueError."""

    normalized = tool_kind.strip().lower()
    aliases = {
        "markdown": "markdown-to-wordpress",
        "md2wp": "markdown-to-wordpress",
        "wordpress-importer": "markdown-to-wordpress",
        "ai": "ai-draft",
        "ai-drafts": "ai-draft",
        "uploader": "media-uploader",
        "media-upload": "media-uploader",
        "gutenberg": "gutenberg-tool",
        "cms": "cms-automation",
        "migration": "static-site-migration",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in PATTERNS:
        supported = ", ".join(SUPPORTED_TOOL_KINDS)
        raise ValueError(f"Unsupported ecosystem tool kind {tool_kind!r}. Supported values: {supported}")
    return normalized


def ecosystem_tool_kinds() -> List[Dict[str, str]]:
    """Return supported ecosystem tool kinds for CLI discovery."""

    return [
        {"tool_kind": key, "label": pattern.label}
        for key, pattern in PATTERNS.items()
    ]


def build_readme_section(pattern: EcosystemPattern, project_name: str) -> str:
    """Build a target-specific README section for an adjacent project."""

    intro = pattern.readme_intro.format(project=project_name)
    return "\n".join([
        f"## {pattern.readme_heading}",
        "",
        intro,
        "",
        (
            "[Pictovap](https://github.com/yoldaolmak/Pictovap) is a CLI-first "
            "companion workflow for this boundary: Markdown article -> visual brief "
            "-> candidate scoring -> provenance pack -> editor report -> CMS "
            "placement plan."
        ),
        "",
        pattern.boundary,
        "",
    ])


def build_pr_body(pattern: EcosystemPattern, project_name: str, repository_url: str | None = None) -> str:
    """Build a concise PR body for an ecosystem documentation contribution."""

    repo_line = f"\n\nTarget repository: {repository_url}" if repository_url else ""
    return "\n".join([
        "Adds a small documentation section for the adjacent image-planning workflow.",
        "",
        f"{project_name} owns: {pattern.owned_by_tool}",
        f"Pictovap can add: {pattern.pictovap_role}",
        "",
        "This is docs-only and does not change runtime behavior.",
        repo_line.strip(),
    ]).strip() + "\n"


def build_workflow_commands() -> List[str]:
    """Return the standard pre-publish workflow commands."""

    return [
        "pictovap plan --article posts/example.md --profile profiles/publisher.yaml "
        "--output artifacts/pictovap-plan.json --report artifacts/pictovap-report.md",
        "pictovap feedback --plan artifacts/pictovap-plan.json --format markdown",
        "pictovap publish --plan artifacts/pictovap-plan.json --cms wordpress --dry-run",
    ]


def build_ecosystem_match(
    tool_kind: str,
    project_name: str = "This project",
    repository_url: str | None = None,
) -> Dict[str, Any]:
    """Build a reusable ecosystem integration packet."""

    normalized = normalize_tool_kind(tool_kind)
    pattern = PATTERNS[normalized]
    clean_project = project_name.strip() or "This project"
    clean_repo = repository_url.strip() if repository_url else None

    return {
        "status": "compatible",
        "tool_kind": pattern.tool_kind,
        "label": pattern.label,
        "project_name": clean_project,
        "repository_url": clean_repo,
        "owned_by_target": pattern.owned_by_tool,
        "pictovap_role": pattern.pictovap_role,
        "boundary": pattern.boundary,
        "workflow": [
            "Draft or Markdown article",
            "Pictovap visual plan and editor report",
            "Editor approval",
            "CMS import, media upload, or publish workflow",
        ],
        "commands": build_workflow_commands(),
        "readme_section": build_readme_section(pattern, clean_project),
        "pr_body": build_pr_body(pattern, clean_project, clean_repo),
        "anti_spam_checklist": [
            "The target repository benefits even if no one clicks the Pictovap link.",
            "Pictovap is framed as a companion workflow, not a replacement.",
            "The wording is specific to the target project's actual publishing boundary.",
            "The Pictovap link appears once.",
            "No SEO, traffic, or complete-automation claims are made.",
        ],
    }


def render_ecosystem_markdown(packet: Dict[str, Any]) -> str:
    """Render an ecosystem integration packet as copyable Markdown."""

    lines: List[str] = [
        "# Pictovap Ecosystem Integration",
        "",
        f"- Target: {packet['project_name']}",
        f"- Tool kind: {packet['tool_kind']}",
        f"- Boundary: {packet['boundary']}",
        "",
        "## README Section",
        "",
        packet["readme_section"].rstrip(),
        "",
        "## Pull Request Body",
        "",
        packet["pr_body"].rstrip(),
        "",
        "## Workflow Commands",
        "",
    ]
    lines.extend(f"- `{command}`" for command in packet["commands"])
    lines.extend(["", "## Anti-Spam Checklist", ""])
    lines.extend(f"- [ ] {item}" for item in packet["anti_spam_checklist"])
    lines.append("")
    return "\n".join(lines)


def render_supported_tool_kinds(kinds: Iterable[Dict[str, str]]) -> str:
    """Render supported ecosystem tool kinds as Markdown."""

    lines = ["# Supported Ecosystem Tool Kinds", ""]
    for item in kinds:
        lines.append(f"- `{item['tool_kind']}` — {item['label']}")
    lines.append("")
    return "\n".join(lines)
