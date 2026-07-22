import json

from pictovap_pixabay import PixabaySource
from pictovap.testing import assert_image_source_contract


def test_adapter_contract_without_credentials():
    adapter = PixabaySource()
    assert assert_image_source_contract(adapter) == []


def test_adapter_maps_mocked_pixabay_response(monkeypatch):
    payload = {"hits": [{
        "id": 42,
        "largeImageURL": "https://cdn.example/pixabay-42.jpg",
        "imageWidth": 1600,
        "imageHeight": 900,
        "tags": "travel, mountain",
        "user": "Example Photographer",
    }]}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(payload).encode()

    monkeypatch.setattr("pictovap_pixabay.urllib.request.urlopen", lambda *args, **kwargs: FakeResponse())
    candidates = assert_image_source_contract(PixabaySource("test-key"), count=1)
    assert candidates[0]["license"] == "pixabay"
    assert candidates[0]["attribution"] == "Example Photographer"


def test_adapter_returns_empty_on_api_failure(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("offline")

    monkeypatch.setattr("pictovap_pixabay.urllib.request.urlopen", fail)
    assert PixabaySource("test-key").search_candidates("mountains", 2) == []
