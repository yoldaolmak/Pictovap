"""Tests for Markdown frontmatter flowing through the visual planning contract."""

import json

from pictovap.core.primitives import VisualBrief
from pictovap.demo import create_visual_plan, generate_markdown_report, score_candidate


def test_markdown_frontmatter_populates_brief_and_serializes(tmp_path):
    article = tmp_path / "article.md"
    article.write_text(
        """---
title: A Weekend in Sinop
tags: [coast, walking]
categories:
  - travel
audience: first-time visitors
location: Sinop
avoid_list: [generic city skyline]
---

# Heading is kept as article content

## Coastline Walk

Start at the harbor and follow the coast.
""",
        encoding="utf-8",
    )

    brief = VisualBrief.from_markdown(str(article))

    assert brief.article_title == "A Weekend in Sinop"
    assert brief.topic == "A Weekend in Sinop"
    assert brief.detected_location == "Sinop"
    assert brief.avoid_list == ["generic city skyline"]
    assert brief.frontmatter["tags"] == ["coast", "walking"]
    assert brief.frontmatter["categories"] == ["travel"]
    assert brief.to_dict()["frontmatter"]["audience"] == "first-time visitors"
    assert len(brief.image_slots) == 2


def test_frontmatter_context_influences_candidate_score(tmp_path):
    article = tmp_path / "article.md"
    article.write_text(
        """---
title: A Quiet Weekend
tags: [coast, walking]
location: Sinop
---

## Harbor Walk
""",
        encoding="utf-8",
    )
    brief = VisualBrief.from_markdown(str(article))
    slot = brief.image_slots[0]
    coastal_candidate = {
        "id": "coastal",
        "keywords": ["coast", "walking", "sinop"],
        "width": 1600,
        "height": 1000,
        "provider": "local",
        "license": "CC0",
    }
    generic_candidate = {
        "id": "generic",
        "keywords": ["generic"],
        "width": 1600,
        "height": 1000,
        "provider": "local",
        "license": "CC0",
    }

    assert score_candidate(coastal_candidate, slot, brief).final_score > score_candidate(
        generic_candidate, slot, brief
    ).final_score


def test_missing_and_malformed_frontmatter_are_safe(tmp_path):
    plain = tmp_path / "plain.md"
    plain.write_text("# Plain Article\n\n## Section\nText", encoding="utf-8")
    malformed = tmp_path / "malformed.md"
    malformed.write_text("---\ntags: [unclosed\n---\n# Still an Article", encoding="utf-8")

    plain_brief = VisualBrief.from_markdown(str(plain))
    malformed_brief = VisualBrief.from_markdown(str(malformed))

    assert plain_brief.frontmatter == {}
    assert plain_brief.article_title == "Plain Article"
    assert malformed_brief.frontmatter == {}
    assert malformed_brief.article_title == "Still an Article"


def test_report_includes_frontmatter_context(tmp_path):
    article = tmp_path / "article.md"
    article.write_text("---\ntags: [coast]\n---\n# Article", encoding="utf-8")
    brief = VisualBrief.from_markdown(str(article))
    report = generate_markdown_report({"visual_brief": brief.to_dict()})

    assert "Frontmatter context" in report
    assert "\"coast\"" in report
    json.dumps(brief.to_dict())


def test_public_plan_preserves_frontmatter_location(tmp_path):
    article = tmp_path / "article.md"
    article.write_text("---\nlocation: Sinop\n---\n# Article", encoding="utf-8")

    plan = create_visual_plan(str(article))

    assert plan["visual_brief"]["detected_location"] == "Sinop"
    assert plan["visual_brief"]["frontmatter"]["location"] == "Sinop"
