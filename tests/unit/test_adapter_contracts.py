"""Protocol-level contract tests for every real adapter.

These tests don't re-test each adapter's internal logic (that's covered by
test_sources.py, test_cms_publishers.py, and test_cms_placement.py) --
they assert the one thing every adapter of a given kind must guarantee,
regardless of implementation:

  * Image source adapters: conform to ImageSourceAdapter, never raise on
    construction, degrade to an empty list (not an exception) when
    unconfigured, and return candidates matching the documented dict shape.
  * CMS adapters: conform to CMSAdapter, raise a clear, actionable error
    when constructed without credentials (CMS adapters are only ever used
    once a caller has actually decided to publish -- unlike image sources,
    they are not expected to silently no-op), and place() always returns
    the {placed, failed, warnings} shape.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from pictovap.core.adapters import CMSAdapter, ImageSourceAdapter
from pictovap.core.primitives import CMSPlacement, PlacementInstruction
from pictovap.providers.deposit import DepositPhotosSource
from pictovap.providers.local import LocalFolderSource
from pictovap.providers.openverse import OpenverseSource
from pictovap.providers.pexels import PexelsSource
from pictovap.providers.unsplash import UnsplashSource
from pictovap.publishers.ghost import GhostPublisher
from pictovap.publishers.strapi import StrapiPublisher

REQUIRED_CANDIDATE_FIELDS = {
    "id", "filename", "provider", "source_type", "local_path", "source_url",
    "license", "attribution", "keywords", "width", "height",
}

# Every image source adapter: must conform to the protocol and never raise
# on construction, credentialed or not.
IMAGE_SOURCE_ADAPTERS = [
    LocalFolderSource, UnsplashSource, DepositPhotosSource, OpenverseSource, PexelsSource,
]
# Subset that is credential-gated: calling search_candidates() with no
# credentials configured must degrade to [] without making a network call.
# Openverse is excluded here because it needs no credentials at all -- an
# unconfigured call to it is a real network request, which is covered with
# a mocked failure in test_openverse_pexels.py instead.
CREDENTIAL_GATED_IMAGE_SOURCES = [UnsplashSource, DepositPhotosSource, PexelsSource]
CMS_ADAPTER_CLASSES = [GhostPublisher, StrapiPublisher]  # constructor-credentialed adapters


# ── Image source adapters ─────────────────────────────────────────────────────

@pytest.mark.parametrize("adapter_cls", IMAGE_SOURCE_ADAPTERS)
def test_image_source_conforms_to_protocol(adapter_cls):
    assert issubclass(adapter_cls, ImageSourceAdapter)


@pytest.mark.parametrize("adapter_cls", IMAGE_SOURCE_ADAPTERS)
def test_image_source_construction_never_requires_credentials(adapter_cls, monkeypatch):
    """Constructing any image source adapter with zero configuration must
    never raise -- missing credentials are only ever an empty-result
    concern, surfaced at search time."""
    monkeypatch.delenv("UNSPLASH_ACCESS_KEY", raising=False)
    monkeypatch.delenv("DEPOSIT_API_KEY", raising=False)
    monkeypatch.delenv("PICTOVAP_LOCAL_IMAGE_DIR", raising=False)
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    instance = adapter_cls()  # must not raise
    assert instance is not None


@pytest.mark.parametrize("adapter_cls", CREDENTIAL_GATED_IMAGE_SOURCES)
def test_image_source_degrades_to_empty_list_when_unconfigured(adapter_cls, monkeypatch):
    monkeypatch.delenv("UNSPLASH_ACCESS_KEY", raising=False)
    monkeypatch.delenv("DEPOSIT_API_KEY", raising=False)
    monkeypatch.delenv("PICTOVAP_LOCAL_IMAGE_DIR", raising=False)
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    instance = adapter_cls()
    assert instance.search_candidates("anything", 5) == []


def test_local_source_candidate_matches_documented_shape(tmp_path):
    from PIL import Image
    img_path = tmp_path / "harbor-view.jpg"
    Image.new("RGB", (1600, 1000), color="blue").save(img_path)

    source = LocalFolderSource(directory=str(tmp_path))
    candidates = source.search_candidates("harbor", 5)

    assert len(candidates) == 1
    candidate = candidates[0]
    missing = REQUIRED_CANDIDATE_FIELDS - candidate.keys()
    assert not missing, f"Candidate missing required fields: {missing}"
    assert isinstance(candidate["width"], int)
    assert isinstance(candidate["height"], int)
    assert isinstance(candidate["keywords"], list)


# ── CMS adapters ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("adapter_cls", CMS_ADAPTER_CLASSES)
def test_cms_adapter_conforms_to_protocol(adapter_cls):
    assert issubclass(adapter_cls, CMSAdapter)


def test_wordpress_conforms_to_cms_adapter_protocol():
    from pictovap.services.wordpress import WordPressUploader
    assert issubclass(WordPressUploader, CMSAdapter)


@pytest.mark.parametrize("adapter_cls,env_keys", [
    (GhostPublisher, ["GHOST_URL", "GHOST_ADMIN_API_KEY"]),
    (StrapiPublisher, ["STRAPI_URL", "STRAPI_API_TOKEN"]),
])
def test_cms_adapter_raises_clear_error_without_credentials(adapter_cls, env_keys, monkeypatch):
    """CMS adapters are only reached once a caller has decided to actually
    publish, so -- unlike image sources -- they are expected to fail loudly
    and clearly at construction time when unconfigured, not silently no-op."""
    for key in env_keys:
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(ValueError):
        adapter_cls()


def test_wordpress_raises_clear_error_without_credentials(monkeypatch):
    from pictovap.services.wordpress import WordPressUploader
    for key in ("WP_URL", "WP_USER", "WP_APP_PASSWORD"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(ValueError, match="Missing WordPress credentials"):
        WordPressUploader(site="demo")


def _one_instruction():
    return [PlacementInstruction(
        slot_id="featured",
        output_path="/tmp/fake.webp",
        image_role="featured",
        alt_text="alt",
        caption="caption",
    )]


def test_ghost_place_returns_documented_result_shape():
    pub = GhostPublisher(ghost_url="https://example.ghost.io", admin_api_key="abc:deadbeef")
    placement = CMSPlacement(article_id="1", placements=_one_instruction())
    with patch.object(pub, "upload_media", return_value={"success": False, "error": "boom"}):
        result = pub.place(placement)
    assert set(result.keys()) == {"placed", "failed", "warnings"}
    assert isinstance(result["placed"], list)
    assert isinstance(result["failed"], list)
    assert isinstance(result["warnings"], list)


def test_strapi_place_returns_documented_result_shape():
    pub = StrapiPublisher(strapi_url="https://cms.example.com", api_token="tok")
    placement = CMSPlacement(article_id="1", placements=_one_instruction())
    with patch.object(pub, "upload_media", return_value={"success": False, "error": "boom"}):
        result = pub.place(placement)
    assert set(result.keys()) == {"placed", "failed", "warnings"}
