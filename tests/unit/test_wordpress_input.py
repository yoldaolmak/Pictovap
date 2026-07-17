from __future__ import annotations

from pictovap.core.primitives import VisualBrief
from pictovap.demo import create_wordpress_visual_plan


GUTENBERG_CONTENT = """
<!-- wp:paragraph -->
<p>Plan a weekend trip with less friction.</p>
<!-- /wp:paragraph -->
<!-- wp:heading -->
<h2>Packing smart</h2>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Choose versatile layers and bring a small day pack.</p>
<!-- /wp:paragraph -->
<!-- wp:heading -->
<h2>Finding quiet trails</h2>
<!-- /wp:heading -->
<p>Start early and check local access rules before leaving.</p>
<!-- /wp:paragraph -->
"""


def test_visual_brief_from_gutenberg_html_preserves_heading_targets():
    brief = VisualBrief.from_html(
        GUTENBERG_CONTENT,
        title="A calmer weekend outdoors",
        article_id=42,
        source_path="wordpress://demo/posts/42",
    )

    assert brief.article_id == "42"
    assert brief.article_title == "A calmer weekend outdoors"
    assert [section["heading"] for section in brief.sections] == [
        "Packing smart",
        "Finding quiet trails",
    ]
    assert brief.image_slots[1]["target_heading"] == "Packing smart"
    assert "versatile layers" in brief.image_slots[1]["section_excerpt"]


def test_wordpress_plan_reads_post_without_writing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "pictovap.services.wordpress.fetch_post_context",
        lambda post_id, site: {
            "id": post_id,
            "title": "A calmer weekend outdoors",
            "content_raw": GUTENBERG_CONTENT,
        },
    )

    plan = create_wordpress_visual_plan(
        42,
        site="publisher",
        output=str(tmp_path / "plan.json"),
    )

    assert plan["source_path"] == "wordpress://publisher/posts/42"
    assert plan["visual_brief"]["article_id"] == "42"
    assert plan["cms_placement"]["article_id"] == "42"
    assert (tmp_path / "plan.json").exists()
