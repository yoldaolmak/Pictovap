"""Unit tests for Ghost and Strapi CMS publisher adapters."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pictovap.publishers.ghost import GhostPublisher
from pictovap.publishers.strapi import StrapiPublisher


# ── GhostPublisher ────────────────────────────────────────────────────────────

class TestGhostPublisher:
    """Tests for GhostPublisher adapter."""

    def test_init_raises_without_credentials(self):
        with pytest.raises(ValueError, match="GHOST_URL"):
            GhostPublisher(ghost_url="", admin_api_key="")

    def test_init_raises_without_api_key(self):
        with pytest.raises(ValueError):
            GhostPublisher(ghost_url="https://example.ghost.io", admin_api_key="")

    def test_upload_media_missing_file_returns_error(self, tmp_path):
        pub = GhostPublisher(
            ghost_url="https://example.ghost.io",
            admin_api_key="abc123:deadbeef00",
        )
        result = pub.upload_media(
            file_path=str(tmp_path / "nonexistent.webp"),
            title="Test",
            alt_text="Test alt",
        )
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_upload_media_calls_admin_images_endpoint(self, tmp_path):
        img = tmp_path / "test.webp"
        img.write_bytes(b"RIFF....WEBP")

        pub = GhostPublisher(
            ghost_url="https://example.ghost.io",
            admin_api_key="abc123:deadbeef0011223344556677889900112233445566778899001122334455",
        )

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"images": [{"url": "https://cdn.ghost.io/img/test.webp"}]}
        mock_resp.raise_for_status = MagicMock()

        with patch.object(pub._session, "post", return_value=mock_resp):
            result = pub.upload_media(str(img), "Test Title", "Alt text")

        assert result["success"] is True
        assert result["url"] == "https://cdn.ghost.io/img/test.webp"
        assert result["media_id"] == "https://cdn.ghost.io/img/test.webp"

    def test_upload_media_returns_error_on_http_failure(self, tmp_path):
        img = tmp_path / "test.webp"
        img.write_bytes(b"RIFF....WEBP")

        pub = GhostPublisher(
            ghost_url="https://example.ghost.io",
            admin_api_key="abc123:deadbeef0011223344556677889900112233445566778899001122334455",
        )

        import requests as req_lib
        with patch.object(pub._session, "post", side_effect=req_lib.RequestException("connection refused")):
            result = pub.upload_media(str(img), "Test", "alt")

        assert result["success"] is False
        assert "connection refused" in result["error"]

    def test_fetch_post_context_returns_structured_dict(self):
        pub = GhostPublisher(
            ghost_url="https://example.ghost.io",
            admin_api_key="abc123:deadbeef0011223344556677889900112233445566778899001122334455",
        )

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "posts": [{
                "title": "Akyaka Travel Guide",
                "slug": "akyaka-travel-guide",
                "html": "<p>Content</p>",
                "plaintext": "Content",
                "tags": [{"name": "Turkey"}, {"name": "Travel"}],
                "status": "published",
            }]
        }

        with patch.object(pub._session, "get", return_value=mock_resp):
            ctx = pub.fetch_post_context("post-uuid-1234")

        assert ctx["title"] == "Akyaka Travel Guide"
        assert ctx["slug"] == "akyaka-travel-guide"
        assert "Turkey" in ctx["tags"]


# ── StrapiPublisher ───────────────────────────────────────────────────────────

class TestStrapiPublisher:
    """Tests for StrapiPublisher adapter."""

    def test_init_raises_without_credentials(self):
        with pytest.raises(ValueError, match="STRAPI_URL"):
            StrapiPublisher(strapi_url="", api_token="")

    def test_upload_media_missing_file_returns_error(self, tmp_path):
        pub = StrapiPublisher(
            strapi_url="https://cms.example.com",
            api_token="tok_abc123",
        )
        result = pub.upload_media(
            file_path=str(tmp_path / "nonexistent.webp"),
            title="Test",
            alt_text="Alt",
        )
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_upload_media_calls_strapi_upload_endpoint(self, tmp_path):
        img = tmp_path / "photo.webp"
        img.write_bytes(b"RIFF....WEBP")

        pub = StrapiPublisher(
            strapi_url="https://cms.example.com",
            api_token="tok_abc123",
        )

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [
            {"id": 42, "url": "/uploads/photo_abc123.webp"}
        ]

        with patch.object(pub._session, "post", return_value=mock_resp):
            result = pub.upload_media(str(img), "Photo Title", "Alt text", caption="A caption")

        assert result["success"] is True
        assert result["media_id"] == 42
        assert "cms.example.com" in result["url"]  # absolute URL built

    def test_upload_media_strapi_v4_absolute_url_passthrough(self, tmp_path):
        """If Strapi already returns an absolute URL, it should not be prefixed again."""
        img = tmp_path / "photo.webp"
        img.write_bytes(b"RIFF....WEBP")

        pub = StrapiPublisher(
            strapi_url="https://cms.example.com",
            api_token="tok_abc123",
        )

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [
            {"id": 7, "url": "https://cdn.example.com/uploads/photo.webp"}
        ]

        with patch.object(pub._session, "post", return_value=mock_resp):
            result = pub.upload_media(str(img), "Title", "Alt")

        assert result["url"] == "https://cdn.example.com/uploads/photo.webp"

    def test_attach_to_post_calls_put_endpoint(self):
        pub = StrapiPublisher(
            strapi_url="https://cms.example.com",
            api_token="tok_abc123",
        )

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()

        with patch.object(pub._session, "put", return_value=mock_resp) as mock_put:
            result = pub.attach_to_post(42, 10, content_type="articles", field_name="cover")

        assert result["success"] is True
        called_url = mock_put.call_args[0][0]
        assert "articles/10" in called_url
        payload = mock_put.call_args[1]["json"]
        assert payload["data"]["cover"] == 42

    def test_fetch_post_context_returns_structured_dict(self):
        pub = StrapiPublisher(
            strapi_url="https://cms.example.com",
            api_token="tok_abc123",
        )

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "id": 10,
                "attributes": {
                    "title": "Akyaka Travel Guide",
                    "slug": "akyaka-travel-guide",
                    "content": "<p>Body</p>",
                    "publishedAt": "2026-07-01T00:00:00.000Z",
                    "tags": {
                        "data": [
                            {"attributes": {"name": "Turkey"}},
                            {"attributes": {"name": "Travel"}},
                        ]
                    },
                },
            }
        }

        with patch.object(pub._session, "get", return_value=mock_resp):
            ctx = pub.fetch_post_context(10)

        assert ctx["title"] == "Akyaka Travel Guide"
        assert ctx["slug"] == "akyaka-travel-guide"
        assert "Turkey" in ctx["tags"]
        assert ctx["status"] == "published"
