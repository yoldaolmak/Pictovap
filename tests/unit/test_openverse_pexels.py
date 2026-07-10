"""Unit tests for the Openverse and Pexels image source adapters."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from pictova.core.adapters import ImageSourceAdapter
from pictova.providers.openverse import OpenverseSource, search_candidates as openverse_search
from pictova.providers.pexels import PexelsSource, search_candidates as pexels_search


# ── Openverse ──────────────────────────────────────────────────────────────────

def test_openverse_conforms_to_protocol():
    assert issubclass(OpenverseSource, ImageSourceAdapter)


def test_openverse_requires_no_credentials_to_construct():
    OpenverseSource()  # must not raise


def test_openverse_returns_empty_list_on_network_error():
    with patch("pictova.providers.openverse.urllib.request.urlopen", side_effect=OSError("refused")):
        assert openverse_search("beach", 5) == []


def test_openverse_parses_real_shaped_response():
    fake_response = {
        "results": [
            {
                "id": "abc-123",
                "title": "Sunset over the bay",
                "creator": "Jane Doe",
                "license": "cc0",
                "url": "https://example.org/photo.jpg",
                "width": 2000,
                "height": 1300,
                "tags": [{"name": "sunset"}, {"name": "bay"}],
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_response).encode()
    mock_resp.__enter__.return_value = mock_resp

    with patch("pictova.providers.openverse.urllib.request.urlopen", return_value=mock_resp):
        candidates = openverse_search("bay", 5)

    assert len(candidates) == 1
    cand = candidates[0]
    assert cand["provider"] == "openverse"
    assert cand["license"] == "cc0"
    assert cand["attribution"] == "Jane Doe"
    assert cand["width"] == 2000
    assert "sunset" in cand["keywords"]


# ── Pexels ─────────────────────────────────────────────────────────────────────

def test_pexels_conforms_to_protocol():
    assert issubclass(PexelsSource, ImageSourceAdapter)


def test_pexels_requires_no_credentials_to_construct():
    PexelsSource()  # must not raise


def test_pexels_returns_empty_list_without_api_key(monkeypatch):
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    assert pexels_search("mountains", 5) == []


def test_pexels_returns_empty_list_on_network_error(monkeypatch):
    monkeypatch.setenv("PEXELS_API_KEY", "test-key")
    with patch("pictova.providers.pexels.urllib.request.urlopen", side_effect=OSError("refused")):
        assert pexels_search("mountains", 5) == []


def test_pexels_parses_real_shaped_response(monkeypatch):
    monkeypatch.setenv("PEXELS_API_KEY", "test-key")
    fake_response = {
        "photos": [
            {
                "id": 555,
                "width": 1920,
                "height": 1080,
                "photographer": "John Smith",
                "alt": "Mountain range at sunrise",
                "src": {"original": "https://images.pexels.com/photos/555/original.jpg"},
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_response).encode()
    mock_resp.__enter__.return_value = mock_resp

    with patch("pictova.providers.pexels.urllib.request.urlopen", return_value=mock_resp):
        candidates = pexels_search("mountains", 5)

    assert len(candidates) == 1
    cand = candidates[0]
    assert cand["provider"] == "pexels"
    assert cand["attribution"] == "John Smith"
    assert cand["source_url"] == "https://images.pexels.com/photos/555/original.jpg"
    assert "Mountain" in cand["keywords"]
