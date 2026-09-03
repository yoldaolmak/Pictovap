"""Stable public Python API for creating Pictovap visual plans."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pictovap.core.primitives import VisualBrief
from pictovap.core.profile import PublisherProfile
from pictovap.data.demo_candidates import MOCK_CANDIDATES
from pictovap.engine.planner import build_visual_plan
from pictovap.engine.reporting import write_plan_artifacts


def _load_profile(profile: str | None) -> PublisherProfile:
    if profile is None:
        return PublisherProfile.get_default_profile()
    profile_path = Path(profile)
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {profile}")
    return PublisherProfile.from_yaml(profile_path)


def create_visual_plan(
    article: str,
    profile: str | None = None,
    *,
    output: str | None = None,
    report: str | None = None,
    provider_adapter: object | None = None,
    provider_name: str | None = None,
    report_renderer: object | None = None,
) -> dict[str, Any]:
    """Create a JSON-shaped visual plan from a Markdown article.

    This is the stable library equivalent of ``pictovap plan``. It performs no
    CMS writes and prints nothing. Pass ``output`` and/or ``report`` only when
    the caller wants files in addition to the returned plan.

    When a profile configures no reachable image source, planning falls back to
    the deterministic fixture candidates and records that fact as
    ``runtime.provider.mode == "demo-fallback"`` in the returned plan.

    Args:
        article: Path to a Markdown article.
        profile: Path to a Publisher Profile YAML. Uses the default profile
            when omitted.
        output: If given, also writes the JSON plan to this path.
        report: If given, also writes an editor report to this path.
        provider_adapter: An already constructed third-party image-source
            adapter. When supplied, its candidates are validated and no
            fallback is used.
        provider_name: Entry-point name recorded in runtime metadata when a
            third-party provider is supplied.
        report_renderer: An installed report renderer. Defaults to the
            built-in Markdown editor report.

    Returns:
        The JSON-shaped visual plan as a dict (visual_brief, fit_scores,
        provenance_packs, cms_placement, intent_proof, ...).

    Raises:
        FileNotFoundError: if ``article`` or ``profile`` doesn't exist.

    Example:
        from pictovap import create_visual_plan

        plan = create_visual_plan(article="article.md", profile="publisher.yaml")
    """
    article_path = Path(article)
    if not article_path.exists():
        raise FileNotFoundError(f"Article not found: {article}")

    plan = build_visual_plan(
        article_path,
        _load_profile(profile),
        use_real_sources=True,
        provider_adapter=provider_adapter,
        provider_name=provider_name,
        fallback_candidates=MOCK_CANDIDATES,
        fallback_mode="demo-fallback",
    )
    if output or report:
        write_plan_artifacts(plan, output, report, report_renderer)
    return plan


def create_wordpress_visual_plan(
    post_id: int,
    *,
    site: str = "demo",
    profile: str | None = None,
    output: str | None = None,
    report: str | None = None,
    provider_adapter: object | None = None,
    provider_name: str | None = None,
    report_renderer: object | None = None,
) -> dict[str, Any]:
    """Create a visual plan from a WordPress Gutenberg post without writes.

    The post is read through the WordPress REST API edit context. No content or
    media is written; publishing remains a separate, explicit operation.
    """
    from pictovap.services.wordpress import fetch_post_context

    post = fetch_post_context(post_id, site=site)
    if not post:
        raise ValueError(f"WordPress post {post_id} could not be read")
    raw_content = str(post.get("content_raw") or "")
    if not raw_content:
        raise ValueError(f"WordPress post {post_id} has no editable content")

    publisher_profile = _load_profile(profile)
    brief = VisualBrief.from_html(
        raw_content,
        title=str(post.get("title") or ""),
        article_id=post_id,
        source_path=f"wordpress://{site}/posts/{post_id}",
        fallback_lang=publisher_profile.language,
    )
    plan = build_visual_plan(
        None,
        publisher_profile,
        use_real_sources=True,
        source_label=brief.source_path,
        provider_adapter=provider_adapter,
        provider_name=provider_name,
        brief=brief,
        fallback_candidates=MOCK_CANDIDATES,
        fallback_mode="demo-fallback",
    )
    if output or report:
        write_plan_artifacts(plan, output, report, report_renderer)
    return plan


__all__ = ["create_visual_plan", "create_wordpress_visual_plan"]
