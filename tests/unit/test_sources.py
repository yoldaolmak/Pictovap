"""Tests for image source adapters and the fetch_candidates orchestrator."""

from PIL import Image

from pictova.core.profile import PublisherProfile
from pictova.core.sources import fetch_candidates
from pictova.providers.local import LocalFolderSource


def test_local_folder_source_returns_empty_when_unconfigured():
    source = LocalFolderSource(directory="")
    assert source.search_candidates("anything", 5) == []


def test_local_folder_source_returns_empty_for_missing_directory(tmp_path):
    source = LocalFolderSource(directory=str(tmp_path / "does-not-exist"))
    assert source.search_candidates("anything", 5) == []


def test_local_folder_source_reads_real_images(tmp_path):
    image_path = tmp_path / "minimalist-travel-guide.jpg"
    Image.new("RGB", (1600, 1000), color="blue").save(image_path)

    source = LocalFolderSource(directory=str(tmp_path))
    candidates = source.search_candidates("travel", 5)

    assert len(candidates) == 1
    cand = candidates[0]
    assert cand["provider"] == "local"
    assert cand["source_type"] == "local"
    assert cand["local_path"] == str(image_path)
    assert cand["width"] == 1600
    assert cand["height"] == 1000


def test_fetch_candidates_falls_back_to_empty_when_nothing_configured(monkeypatch):
    monkeypatch.delenv("UNSPLASH_ACCESS_KEY", raising=False)
    monkeypatch.delenv("DEPOSIT_API_KEY", raising=False)
    monkeypatch.delenv("PICTOVAP_LOCAL_IMAGE_DIR", raising=False)

    profile = PublisherProfile(
        profile_id="test",
        brand_name="Test Publisher",
        image_sources=["local", "unsplash", "deposit"],
    )
    assert fetch_candidates(profile, query="travel", count=5) == []


def test_fetch_candidates_uses_local_source_when_configured(tmp_path, monkeypatch):
    image_path = tmp_path / "travel-photo.jpg"
    Image.new("RGB", (2000, 1300), color="red").save(image_path)
    monkeypatch.setenv("PICTOVAP_LOCAL_IMAGE_DIR", str(tmp_path))

    profile = PublisherProfile(
        profile_id="test",
        brand_name="Test Publisher",
        image_sources=["local"],
    )
    candidates = fetch_candidates(profile, query="travel", count=5)

    assert len(candidates) == 1
    assert candidates[0]["provider"] == "local"


def test_fetch_candidates_skips_unknown_source_names():
    profile = PublisherProfile(
        profile_id="test",
        brand_name="Test Publisher",
        image_sources=["openverse"],  # documented as planned, not yet implemented
    )
    assert fetch_candidates(profile, query="travel", count=5) == []
