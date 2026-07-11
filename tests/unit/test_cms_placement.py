"""Contract tests for CMSAdapter.place() across all three CMS integrations.

These tests exercise the `place(placement: CMSPlacement) -> dict` method that
makes GhostPublisher, StrapiPublisher, and WordPressUploader conform to the
`CMSAdapter` protocol (src/pictova/core/adapters.py). No network calls are
made; every HTTP boundary is mocked.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from pictova.core.adapters import CMSAdapter
from pictova.core.primitives import CMSPlacement, PlacementInstruction
from pictova.publishers.ghost import GhostPublisher
from pictova.publishers.strapi import StrapiPublisher


def _two_instructions() -> list[PlacementInstruction]:
    return [
        PlacementInstruction(
            slot_id="featured",
            output_path="/tmp/pictovap_featured.webp",
            placement_strategy="featured",
            image_role="featured",
            alt_text="A featured image",
            caption="Featured caption",
        ),
        PlacementInstruction(
            slot_id="section_0",
            output_path="/tmp/pictovap_section0.webp",
            target_section="Packing Smart",
            placement_strategy="after_heading",
            image_role="content",
            alt_text="A content image",
            caption="Content caption",
        ),
    ]


# ── Protocol conformance ──────────────────────────────────────────────────────

def test_ghost_strapi_conform_to_cms_adapter_protocol():
    assert issubclass(GhostPublisher, CMSAdapter)
    assert issubclass(StrapiPublisher, CMSAdapter)


def test_wordpress_conforms_to_cms_adapter_protocol():
    from pictova.services.wordpress import WordPressUploader
    assert issubclass(WordPressUploader, CMSAdapter)


# ── GhostPublisher.place() ────────────────────────────────────────────────────

class TestGhostPlace:
    def _pub(self):
        return GhostPublisher(
            ghost_url="https://example.ghost.io",
            admin_api_key="abc123:deadbeef00",
        )

    def test_place_uploads_and_attaches_each_placement(self):
        pub = self._pub()
        placement = CMSPlacement(
            article_id="post-uuid-1",
            adapter_target="ghost",
            target_platform="ghost",
            placements=_two_instructions(),
        )

        with patch.object(pub, "upload_media") as mock_upload, \
                patch.object(pub, "attach_to_post") as mock_attach:
            mock_upload.side_effect = [
                {"success": True, "media_id": "url-1", "url": "url-1"},
                {"success": True, "media_id": "url-2", "url": "url-2"},
            ]
            mock_attach.return_value = {"success": True}
            result = pub.place(placement)

        assert len(result["placed"]) == 2
        assert result["failed"] == []
        assert any("appends every image" in w for w in result["warnings"])
        assert mock_attach.call_count == 2

    def test_place_reports_upload_failure_without_attaching(self):
        pub = self._pub()
        placement = CMSPlacement(article_id="post-uuid-1", placements=_two_instructions()[:1])

        with patch.object(pub, "upload_media") as mock_upload, \
                patch.object(pub, "attach_to_post") as mock_attach:
            mock_upload.return_value = {"success": False, "error": "connection refused"}
            result = pub.place(placement)

        assert result["placed"] == []
        assert result["failed"][0]["stage"] == "upload"
        mock_attach.assert_not_called()

    def test_place_reports_attach_failure(self):
        pub = self._pub()
        placement = CMSPlacement(article_id="post-uuid-1", placements=_two_instructions()[:1])

        with patch.object(pub, "upload_media") as mock_upload, \
                patch.object(pub, "attach_to_post") as mock_attach:
            mock_upload.return_value = {"success": True, "media_id": "url-1", "url": "url-1"}
            mock_attach.return_value = {"success": False, "error": "422 post not found"}
            result = pub.place(placement)

        assert result["placed"] == []
        assert result["failed"][0]["stage"] == "attach"


# ── StrapiPublisher.place() ───────────────────────────────────────────────────

class TestStrapiPlace:
    def _pub(self):
        return StrapiPublisher(strapi_url="https://cms.example.com", api_token="tok_abc123")

    def test_place_single_placement_has_no_warnings(self):
        pub = self._pub()
        placement = CMSPlacement(article_id="10", placements=_two_instructions()[:1])

        with patch.object(pub, "upload_media") as mock_upload, \
                patch.object(pub, "attach_to_post") as mock_attach:
            mock_upload.return_value = {"success": True, "media_id": 42, "url": "https://cms.example.com/x.webp"}
            mock_attach.return_value = {"success": True}
            result = pub.place(placement)

        assert len(result["placed"]) == 1
        assert result["warnings"] == []
        mock_attach.assert_called_once_with(
            42, "10", content_type="articles", field_name="cover",
        )

    def test_place_warns_when_multiple_placements_share_one_field(self):
        pub = self._pub()
        placement = CMSPlacement(article_id="10", placements=_two_instructions())

        with patch.object(pub, "upload_media") as mock_upload, \
                patch.object(pub, "attach_to_post") as mock_attach:
            mock_upload.side_effect = [
                {"success": True, "media_id": 1, "url": "u1"},
                {"success": True, "media_id": 2, "url": "u2"},
            ]
            mock_attach.return_value = {"success": True}
            result = pub.place(placement)

        assert len(result["placed"]) == 2
        assert any("only the last placement" in w for w in result["warnings"])

    def test_place_respects_constructor_content_type_and_field(self):
        pub = StrapiPublisher(
            strapi_url="https://cms.example.com",
            api_token="tok_abc123",
            content_type="posts",
            field_name="hero_image",
        )
        placement = CMSPlacement(article_id="5", placements=_two_instructions()[:1])

        with patch.object(pub, "upload_media") as mock_upload, \
                patch.object(pub, "attach_to_post") as mock_attach:
            mock_upload.return_value = {"success": True, "media_id": 9, "url": "u"}
            mock_attach.return_value = {"success": True}
            pub.place(placement)

        mock_attach.assert_called_once_with(
            9, "5", content_type="posts", field_name="hero_image",
        )


# ── WordPressUploader.place() ───────────────────────────────────────────────

class TestWordPressPlace:
    def _pub(self, monkeypatch):
        monkeypatch.setenv("WP_URL", "https://example.com")
        monkeypatch.setenv("WP_USER", "editor")
        monkeypatch.setenv("WP_APP_PASSWORD", "app-password-value")
        from pictova.services.wordpress import WordPressUploader
        return WordPressUploader(site="demo")

    def test_place_delegates_to_upload_images_batch(self, monkeypatch):
        pub = self._pub(monkeypatch)
        placement = CMSPlacement(article_id="123", placements=_two_instructions())

        fake_batch_result = {
            "uploaded": [
                {"file": "pictovap_featured.webp", "media_id": 1, "url": "u1", "title": "featured"},
                {"file": "pictovap_section0.webp", "media_id": 2, "url": "u2", "title": "section_0"},
            ],
            "failed": [],
            "media_guard": {"status": "ok"},
            "content_update": {"success": True, "updated": True, "inserted": 2},
        }

        with patch("pictova.services.wordpress.upload_images_batch", return_value=fake_batch_result) as mock_batch:
            result = pub.place(placement)

        mock_batch.assert_called_once()
        _, kwargs = mock_batch.call_args
        assert kwargs["post_id"] == 123
        assert kwargs["site"] == "demo"
        assert set(kwargs["metadata_dict"].keys()) == {
            "/tmp/pictovap_featured.webp", "/tmp/pictovap_section0.webp",
        }

        assert len(result["placed"]) == 2
        assert {p["slot_id"] for p in result["placed"]} == {"featured", "section_0"}
        assert result["failed"] == []
        assert result["warnings"] == []

    def test_place_surfaces_attach_errors_as_failed(self, monkeypatch):
        pub = self._pub(monkeypatch)
        placement = CMSPlacement(article_id="123", placements=_two_instructions()[:1])

        fake_batch_result = {
            "uploaded": [
                {"file": "pictovap_featured.webp", "media_id": 1, "attach_error": "404", "title": "featured"},
            ],
            "failed": [],
            "media_guard": {"status": "ok"},
            "content_update": {"success": True, "updated": False},
        }

        with patch("pictova.services.wordpress.upload_images_batch", return_value=fake_batch_result):
            result = pub.place(placement)

        assert result["placed"] == []
        assert len(result["failed"]) == 1
        assert result["failed"][0]["error"] == "404"

    def test_place_rejects_non_numeric_article_id_without_calling_batch(self, monkeypatch):
        pub = self._pub(monkeypatch)
        placement = CMSPlacement(article_id="not-a-post-id", placements=_two_instructions()[:1])

        with patch("pictova.services.wordpress.upload_images_batch") as mock_batch:
            result = pub.place(placement)

        mock_batch.assert_not_called()
        assert result["placed"] == []
        assert result["failed"] == []
        assert "not a valid WordPress post ID" in result["warnings"][0]

    def test_place_warns_on_media_guard_drift(self, monkeypatch):
        pub = self._pub(monkeypatch)
        placement = CMSPlacement(article_id="123", placements=_two_instructions()[:1])

        fake_batch_result = {
            "uploaded": [],
            "failed": [{"error": "Post media integrity check failed before upload"}],
            "media_guard": {"status": "drift"},
        }

        with patch("pictova.services.wordpress.upload_images_batch", return_value=fake_batch_result):
            result = pub.place(placement)

        assert any("drift" in w for w in result["warnings"])
