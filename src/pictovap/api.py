"""Stable public Python API for creating Pictovap visual plans."""

from __future__ import annotations

import contextlib
import io
from pathlib import Path
from typing import Any

from pictovap.core.primitives import VisualBrief
from pictovap.core.profile import PublisherProfile


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

    This is the stable library equivalent of ``pictovap plan``. It performs
    no CMS writes. Pass ``output`` and/or ``report`` only when the caller
    wants files in addition to the returned plan.
    """
    article_path = Path(article)
    if not article_path.exists():
        raise FileNotFoundError(f"Article not found: {article}")

    from pictovap.demo import _build_plan_output, _write_plan_files

    with contextlib.redirect_stdout(io.StringIO()):
        plan = _build_plan_output(
            article_path,
            _load_profile(profile),
            use_real_sources=True,
            provider_adapter=provider_adapter,
            provider_name=provider_name,
        )
    if output or report:
        _write_plan_files(plan, output, report, report_renderer)
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
    """Create a visual plan from a WordPress Gutenberg post without writes."""
    from pictovap.demo import _build_plan_output, _write_plan_files
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
    with contextlib.redirect_stdout(io.StringIO()):
        plan = _build_plan_output(
            None,
            publisher_profile,
            use_real_sources=True,
            source_label=brief.source_path,
            provider_adapter=provider_adapter,
            provider_name=provider_name,
            brief=brief,
        )
    if output or report:
        _write_plan_files(plan, output, report, report_renderer)
    return plan


__all__ = ["create_visual_plan", "create_wordpress_visual_plan"]
