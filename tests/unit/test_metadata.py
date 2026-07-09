"""metadata.py unit testleri — DB cache + vision chain entegrasyonu."""
from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def _make_minimal_db(path: str, with_scanned: bool = True) -> None:
    con = sqlite3.connect(path)
    con.execute("""
        CREATE TABLE asset_index (
            source_id TEXT PRIMARY KEY,
            source_path TEXT NOT NULL DEFAULT '',
            ai_keywords_json TEXT NOT NULL DEFAULT '[]',
            scene TEXT NOT NULL DEFAULT '',
            activity TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            vision_scan_status TEXT NOT NULL DEFAULT 'pending'
        )
    """)
    if with_scanned:
        con.execute("""
            INSERT INTO asset_index VALUES (
                'test-uuid', '/fake/photo.heic',
                '["sinop","castle","coast"]', 'coast', 'travel',
                'Sinop kale manzarası', 'done'
            )
        """)
    con.commit()
    con.close()


def test_db_cached_metadata_returns_data(tmp_path):
    db = str(tmp_path / "test.db")
    _make_minimal_db(db)
    from pictova.engine.metadata import _db_cached_metadata
    with patch("pictova.config.get_visual_memory_db_path", return_value=Path(db)):
        result = _db_cached_metadata("/fake/photo.heic")
    assert result is not None
    assert "sinop" in result["keywords"]
    assert result["scene"] == "coast"


def test_db_cached_metadata_returns_none_for_pending(tmp_path):
    db = str(tmp_path / "test.db")
    _make_minimal_db(db, with_scanned=False)
    con = sqlite3.connect(db)
    con.execute("INSERT INTO asset_index VALUES ('uuid2','/other.heic','[]','','','','pending')")
    con.commit()
    con.close()
    from pictova.engine.metadata import _db_cached_metadata
    with patch("pictova.config.get_visual_memory_db_path", return_value=Path(db)):
        result = _db_cached_metadata("/other.heic")
    assert result is None


def test_enrich_from_cache_builds_metadata():
    from pictova.engine.metadata import _enrich_from_cache
    cached = {"keywords": ["sinop", "castle"], "scene": "coast", "summary": "Sinop kalesi", "activity": "travel"}
    post_ctx = {"title": "Sinop Gezisi"}
    result = _enrich_from_cache(cached, post_ctx)
    assert "alt" in result and len(result["alt"]) > 0
    assert "title" in result and len(result["title"]) > 0
    assert result["source"] == "db_cache"
    assert len(result["alt"]) <= 125
    assert len(result["title"]) <= 60


def test_build_native_metadata_map_uses_cache(tmp_path):
    """Vision chain çağrılmadan DB cache'i kullanır."""
    db = str(tmp_path / "test.db")
    _make_minimal_db(db)
    fake_img = tmp_path / "photo.heic"
    fake_img.write_bytes(b"fake")

    # DB'de source_path eşleşmesi için fake path kullan
    con = sqlite3.connect(db)
    con.execute("UPDATE asset_index SET source_path = ?", [str(fake_img)])
    con.commit()
    con.close()

    from pictova.engine.metadata import build_native_metadata_map

    with patch("pictova.config.get_visual_memory_db_path", return_value=Path(db)), \
         patch("pictova.engine.metadata.has_any_vision_source", return_value=True), \
         patch("pictova.engine.metadata.analyze_image_vision_chain") as mock_chain:
        meta, warnings = build_native_metadata_map(
            [str(fake_img)],
            post_context={"title": "Sinop Gezisi"},
        )

    # Vision chain çağrılmamalı
    mock_chain.assert_not_called()
    assert str(fake_img) in meta
    assert "db_cache" in str(warnings)


def test_build_native_metadata_map_falls_back_to_vision(tmp_path):
    """Cache yoksa vision chain çağrılır."""
    db = str(tmp_path / "empty.db")
    _make_minimal_db(db, with_scanned=False)
    fake_img = tmp_path / "photo.jpg"
    fake_img.write_bytes(b"fake")

    from pictova.engine.metadata import build_native_metadata_map

    mock_result = {
        "alt": "a" * 20,
        "title": "T" * 10,
        "caption": "Karaburun'da bu görselde akşam ışığı kıyıya vuruyor.",
        "description": "D" * 25,
        "keywords": ["kıyı"],
        "scene": "coast",
    }
    with patch("pictova.config.get_visual_memory_db_path", return_value=Path(db)), \
         patch("pictova.engine.metadata.has_any_vision_source", return_value=True), \
         patch("pictova.engine.metadata.analyze_image_vision_chain", return_value=dict(mock_result)) as mock_chain:
        meta, _ = build_native_metadata_map(
            [str(fake_img)],
            post_context={},
        )

    mock_chain.assert_called_once()
    caption = meta[str(fake_img)]["caption"].lower()
    assert "görselde" not in caption
    assert caption == "karaburun'da akşam ışığı kıyıya vuruyor."
