"""selector.py unit testleri."""
from __future__ import annotations

from unittest.mock import patch

import pytest


def test_extract_location_from_slug():
    from pictova.engine.selector import _extract_location
    assert _extract_location({"slug": "antalya-kalkan-koyu"}) == "antalya kalkan koyu"


def test_extract_location_from_title():
    from pictova.engine.selector import _extract_location
    assert _extract_location({"title": "Sinop Gezisi"}) == "Sinop Gezisi"


def test_extract_location_slug_wins_over_title():
    from pictova.engine.selector import _extract_location
    result = _extract_location({"slug": "sinop-kalesi", "title": "Anything"})
    assert result == "sinop kalesi"


def test_destination_index_uuids_match(tmp_path):
    import json
    from pictova.engine.selector import _destination_index_uuids
    idx = {"Sinop": ["uuid-1", "uuid-2", "uuid-3"], "Antalya": ["uuid-4"]}
    idx_file = tmp_path / "destination_index.json"
    idx_file.write_text(json.dumps(idx))
    with patch("pictova.engine.selector.get_visual_memory_db_path") as mock_db:
        mock_db.return_value = type("P", (), {"parent": tmp_path})()
        result = _destination_index_uuids("sinop", 2)
    assert result == ["icloud://uuid-1", "icloud://uuid-2"]


def test_destination_index_uuids_no_match(tmp_path):
    import json
    from pictova.engine.selector import _destination_index_uuids
    idx = {"Sinop": ["uuid-1"]}
    idx_file = tmp_path / "destination_index.json"
    idx_file.write_text(json.dumps(idx))
    with patch("pictova.engine.selector.get_visual_memory_db_path") as mock_db:
        mock_db.return_value = type("P", (), {"parent": tmp_path})()
        result = _destination_index_uuids("istanbul", 3)
    assert result == []


def test_resolve_source_images_semantic():
    from pictova.engine.selector import resolve_source_images
    with patch("pictova.engine.selector.search_semantic_assets", return_value=["/a.jpg", "/b.jpg"]):
        result = resolve_source_images(
            source="semantic", count=2, name=None, query=None,
            location_query="test", content_filter=None, post_context={},
        )
    assert result["source"] == "semantic"
    assert len(result["files"]) == 2


def test_resolve_source_images_unsupported_source():
    from pictova.engine.selector import resolve_source_images
    with pytest.raises(ValueError, match="Unsupported source"):
        resolve_source_images(
            source="nonexistent", count=1, name=None, query=None,
            location_query=None, content_filter=None, post_context={},
        )
