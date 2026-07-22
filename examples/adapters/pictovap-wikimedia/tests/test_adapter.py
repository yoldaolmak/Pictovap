import json

from pictovap_wikimedia import WikimediaSource
from pictovap.testing import assert_image_source_contract


def test_adapter_contract_without_credentials():
    adapter = WikimediaSource()
    assert assert_image_source_contract(adapter, count=0) == []


def test_adapter_maps_mocked_wikimedia_response(monkeypatch):
    payload = {"query": {"pages": [{
        "pageid": 7,
        "title": "File:Mountain.jpg",
        "imageinfo": [{
            "url": "https://upload.wikimedia.org/mountain.jpg",
            "width": 1200,
            "height": 800,
            "extmetadata": {
                "LicenseShortName": {"value": "CC BY-SA 4.0"},
                "Artist": {"value": "<b>Example Artist</b>"},
            },
        }],
    }]}}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(payload).encode()

    monkeypatch.setattr("pictovap_wikimedia.urllib.request.urlopen", lambda *args, **kwargs: FakeResponse())
    candidates = assert_image_source_contract(WikimediaSource(), query="mountain", count=1)
    assert candidates[0]["license"] == "CC BY-SA 4.0"
    assert candidates[0]["attribution"] == "Example Artist"


def test_adapter_skips_incomplete_items(monkeypatch):
    payload = {"query": {"pages": [{
        "pageid": 7,
        "title": "File:Missing-size.jpg",
        "imageinfo": [{"url": "https://upload.wikimedia.org/missing.jpg"}],
    }]}}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(payload).encode()

    monkeypatch.setattr("pictovap_wikimedia.urllib.request.urlopen", lambda *args, **kwargs: FakeResponse())
    assert WikimediaSource().search_candidates("mountain", 1) == []
