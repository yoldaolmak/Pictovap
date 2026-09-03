from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from pictovap.core.primitives import VisualBrief
from pictovap.api import create_wordpress_visual_plan
from pictovap.services.wordpress import WordPressPostReadError


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


def test_visual_brief_from_gutenberg_html_flattens_inline_heading_markup():
    content = """
    <!-- wp:heading -->
    <h2>Walk<strong>ing</strong> the <a href="/coast">coastal route</a></h2>
    <!-- /wp:heading -->
    <p>Follow the marked path.</p>
    <!-- wp:heading {"level":3} -->
    <h3>Pack <em>light</em>, stay longer</h3>
    <!-- /wp:heading -->
    """

    brief = VisualBrief.from_html(content, title="Coastal guide")

    assert [section["heading"] for section in brief.sections] == [
        "Walking the coastal route",
        "Pack light, stay longer",
    ]
    assert brief.image_slots[1]["target_heading"] == "Walking the coastal route"


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


@pytest.mark.parametrize(
    ("status_code", "expected_reason"),
    [
        (401, "authentication failed"),
        (403, "permission denied"),
    ],
)
def test_wordpress_plan_reports_safe_access_errors(monkeypatch, tmp_path, status_code, expected_reason):
    monkeypatch.setenv("PUBLISHER_URL", "https://private.example.test")
    monkeypatch.setenv("PUBLISHER_USER", "editor@example.test")
    monkeypatch.setenv("PUBLISHER_APP_PASSWORD", "fake-secret-password")

    response = MagicMock(status_code=status_code)
    response.text = "private draft content"
    response.raise_for_status.side_effect = requests.HTTPError(response=response)

    with patch("requests.Session.get", return_value=response):
        with pytest.raises(WordPressPostReadError) as exc_info:
            create_wordpress_visual_plan(
                42,
                site="publisher",
                output=str(tmp_path / "plan.json"),
            )

    message = str(exc_info.value)
    assert "WordPress post 42" in message
    assert expected_reason in message
    assert str(status_code) in message
    assert "https://private.example.test" not in message
    assert "editor@example.test" not in message
    assert "fake-secret-password" not in message
    assert "private draft content" not in message
    assert not (tmp_path / "plan.json").exists()


def test_wordpress_plan_reports_missing_post_safely(monkeypatch, tmp_path):
    monkeypatch.setenv("PUBLISHER_URL", "https://private.example.test")
    monkeypatch.setenv("PUBLISHER_USER", "editor@example.test")
    monkeypatch.setenv("PUBLISHER_APP_PASSWORD", "fake-secret-password")

    response = MagicMock(status_code=404)
    response.text = '{"message": "Private post details"}'
    response.raise_for_status.side_effect = requests.HTTPError(response=response)

    with patch("requests.Session.get", return_value=response):
        with pytest.raises(WordPressPostReadError) as exc_info:
            create_wordpress_visual_plan(
                987,
                site="publisher",
                output=str(tmp_path / "plan.json"),
            )

    message = str(exc_info.value)
    assert message == "WordPress post 987 was not found (HTTP 404)"
    assert "Private post details" not in message
    assert not (tmp_path / "plan.json").exists()


def _heading_block(text, level=2):
    return (
        f"<!-- wp:heading -->\n<h{level}>{text}</h{level}>\n<!-- /wp:heading -->\n"
        "<!-- wp:paragraph -->\n<p>body</p>\n<!-- /wp:paragraph -->"
    )


def test_heading_insertion_prefers_the_exact_heading_over_an_earlier_superstring():
    """Targeting 'Tips' must not land under an earlier 'Tips for Packing'."""
    from pictovap.services.wordpress import _insert_block_after_heading

    content = _heading_block("Tips for Packing") + "\n" + _heading_block("Tips")
    updated = _insert_block_after_heading(
        content, heading_text="Tips", block_html="<!-- BLOCK -->"
    )

    assert "<!-- BLOCK -->" in updated
    assert updated.index("<!-- BLOCK -->") > updated.index("<h2>Tips</h2>")


def test_heading_insertion_still_falls_back_to_a_substring_match():
    from pictovap.services.wordpress import _insert_block_after_heading

    content = _heading_block("Packing Smart for Long Trips")
    updated = _insert_block_after_heading(
        content, heading_text="Packing Smart", block_html="<!-- BLOCK -->"
    )

    assert "<!-- BLOCK -->" in updated


def test_heading_insertion_fails_closed_on_an_empty_target():
    """An empty target would otherwise match the first heading in a live post."""
    from pictovap.services.wordpress import _insert_block_after_heading

    content = _heading_block("Introduction") + "\n" + _heading_block("Conclusion")
    for empty in ("", "   ", "\n"):
        assert _insert_block_after_heading(
            content, heading_text=empty, block_html="<!-- BLOCK -->"
        ) == content


def test_upload_media_declares_the_file_s_own_content_type(monkeypatch, tmp_path):
    """A PNG must not be uploaded to the media library announced as WebP."""
    from pictovap.services import wordpress

    monkeypatch.setenv("WP_URL", "https://example.test")
    monkeypatch.setenv("WP_USER", "editor")
    monkeypatch.setenv("WP_APP_PASSWORD", "secret")

    image = tmp_path / "photo.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")
    sent = {}

    class _Response:
        status_code = 201

        def raise_for_status(self):
            return None

        def json(self):
            return {"id": 7, "source_url": "https://example.test/photo.png"}

    class _Session:
        auth = None
        headers: dict = {}

        def post(self, url, **kwargs):
            if "headers" in kwargs:
                sent.update(kwargs["headers"])
            return _Response()

    monkeypatch.setattr(wordpress.WordPressUploader, "_create_session", lambda self: _Session())
    result = wordpress.WordPressUploader(site="demo").upload_media(
        str(image), title="Photo", alt_text="A photo"
    )

    assert result["success"] is True
    assert sent["Content-Type"] == "image/png"
