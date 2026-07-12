"""Tests for image source adapters and the fetch_candidates orchestrator."""

from unittest.mock import patch

from PIL import Image

from pictovap.core.adapters import ImageSourceAdapter
from pictovap.core.profile import PublisherProfile
from pictovap.core.sources import fetch_candidates
from pictovap.providers.deposit import DepositPhotosSource
from pictovap.providers.local import LocalFolderSource
from pictovap.providers.openverse import OpenverseSource
from pictovap.providers.pexels import PexelsSource
from pictovap.providers.unsplash import UnsplashSource


def test_all_source_adapters_conform_to_protocol():
    assert issubclass(LocalFolderSource, ImageSourceAdapter)
    assert issubclass(UnsplashSource, ImageSourceAdapter)
    assert issubclass(DepositPhotosSource, ImageSourceAdapter)
    assert issubclass(OpenverseSource, ImageSourceAdapter)
    assert issubclass(PexelsSource, ImageSourceAdapter)


def test_unsplash_construction_never_raises_without_credentials(monkeypatch):
    """Per the ImageSourceAdapter contract, missing credentials must only
    ever surface as an empty result — never as a raised exception from
    __init__ or search_candidates()."""
    monkeypatch.delenv("UNSPLASH_ACCESS_KEY", raising=False)
    source = UnsplashSource()  # must not raise
    assert source.search_candidates("travel", 5) == []


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


def test_local_folder_source_reads_exif_metadata(tmp_path):
    image_path = tmp_path / "exif-travel.jpg"
    img = Image.new("RGB", (100, 100), color="blue")
    exif = img.getexif()
    # 271 is Make, 272 is Model
    exif[271] = "FakeCamera"
    exif[272] = "ModelX"
    img.save(image_path, exif=exif)

    source = LocalFolderSource(directory=str(tmp_path))
    candidates = source.search_candidates("exif", 5)

    assert len(candidates) == 1
    cand = candidates[0]
    assert "exif" in cand
    assert cand["exif"].get("Make") == "FakeCamera"
    assert cand["exif"].get("Model") == "ModelX"


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
        image_sources=["pixabay"],  # documented as a good-first-issue, not yet implemented
    )
    assert fetch_candidates(profile, query="travel", count=5) == []


def test_fetch_candidates_uses_openverse_when_configured():
    """Openverse needs no credentials, so this exercises fetch_candidates()
    against a mocked network layer rather than a real request."""
    fake_response = {
        "results": [
            {
                "id": "xyz",
                "creator": "A. Photographer",
                "license": "cc0",
                "url": "https://example.org/a.jpg",
                "width": 1200,
                "height": 800,
                "tags": [],
            }
        ]
    }
    import json
    from unittest.mock import MagicMock

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_response).encode()
    mock_resp.__enter__.return_value = mock_resp

    profile = PublisherProfile(
        profile_id="test",
        brand_name="Test Publisher",
        image_sources=["openverse"],
    )
    with patch("pictovap.providers.openverse.urllib.request.urlopen", return_value=mock_resp):
        candidates = fetch_candidates(profile, query="travel", count=5)

    assert len(candidates) == 1
    assert candidates[0]["provider"] == "openverse"
