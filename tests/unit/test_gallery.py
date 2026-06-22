"""gallery_search ve gallery_stats unit testleri."""
from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def _make_test_db(path: str) -> None:
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE asset_index (
            source_id TEXT PRIMARY KEY,
            source_type TEXT NOT NULL DEFAULT 'mac_photos',
            source_path TEXT NOT NULL DEFAULT '',
            folder_path TEXT NOT NULL DEFAULT '',
            filename TEXT NOT NULL DEFAULT '',
            file_extension TEXT NOT NULL DEFAULT '',
            checksum TEXT NOT NULL DEFAULT '',
            width INTEGER, height INTEGER,
            created_at TEXT, camera_make TEXT, camera_model TEXT,
            city TEXT, country TEXT, latitude REAL, longitude REAL,
            album_names_json TEXT NOT NULL DEFAULT '[]',
            title TEXT, description TEXT,
            summary TEXT NOT NULL DEFAULT '',
            scene TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            activity TEXT NOT NULL DEFAULT '',
            objects_json TEXT NOT NULL DEFAULT '[]',
            ai_keywords_json TEXT NOT NULL DEFAULT '[]',
            places_json TEXT NOT NULL DEFAULT '[]',
            people_json TEXT NOT NULL DEFAULT '[]',
            story_tags_json TEXT NOT NULL DEFAULT '[]',
            quality_score REAL NOT NULL DEFAULT 0,
            orientation TEXT NOT NULL DEFAULT '',
            capture_context TEXT NOT NULL DEFAULT '',
            selection_score REAL NOT NULL DEFAULT 0,
            is_personal INTEGER NOT NULL DEFAULT 0,
            personal_reason TEXT NOT NULL DEFAULT '',
            vision_scan_status TEXT NOT NULL DEFAULT 'pending',
            vision_last_scanned_at TEXT,
            vision_last_error TEXT,
            scene_ml TEXT, time_of_day TEXT,
            metadata_keywords_json TEXT NOT NULL DEFAULT '[]',
            exif_metadata_json TEXT NOT NULL DEFAULT '{}',
            raw_metadata_json TEXT NOT NULL DEFAULT '{}',
            state_province TEXT, sub_admin_area TEXT
        );
        CREATE VIRTUAL TABLE asset_search USING fts5(
            source_id UNINDEXED, document, tokenize = 'unicode61'
        );
    """)
    # Test kayıtları
    photos = [
        ("uuid-sinop-1", "/path/sinop1.jpg", "sinop1.jpg", "Sinop", "Sinop", "Türkiye", 0.8, "done", '["castle","coast"]', "landscape"),
        ("uuid-sinop-2", "/path/sinop2.jpg", "sinop2.jpg", "Sinop", "Sinop", "Türkiye", 0.6, "pending", "[]", "landscape"),
        ("uuid-antalya-1", "", "antalya1.heic", "Antalya", "Antalya", "Türkiye", 0.9, "pending", "[]", "landscape"),
    ]
    for uid, src, fn, city, state, country, quality, status, kws, orientation in photos:
        con.execute("""
            INSERT INTO asset_index (source_id, source_path, filename, city, state_province,
            country, quality_score, vision_scan_status, ai_keywords_json, orientation, is_personal)
            VALUES (?,?,?,?,?,?,?,?,?,?,0)
        """, [uid, src, fn, city, state, country, quality, status, kws, orientation])
        doc = f"{city} {state} {country}"
        con.execute("INSERT INTO asset_search (source_id, document) VALUES (?,?)", [uid, doc])
    con.commit()
    con.close()


@pytest.fixture()
def test_db(tmp_path):
    db_path = str(tmp_path / "test_visual_memory.db")
    _make_test_db(db_path)
    return db_path


def test_gallery_search_returns_local_only(test_db):
    from src.pictova.engine.gallery import gallery_search
    with patch("src.pictova.engine.gallery.get_visual_memory_db_path", return_value=Path(test_db)):
        results = gallery_search("sinop", count=10, only_local=True)
    # Sinop'ta 2 lokal fotoğraf var (source_path dolu)
    assert len(results) == 2
    assert all(r["source_path"] != "" for r in results)


def test_gallery_search_includes_icloud_when_not_only_local(test_db):
    from src.pictova.engine.gallery import gallery_search
    with patch("src.pictova.engine.gallery.get_visual_memory_db_path", return_value=Path(test_db)):
        results = gallery_search("antalya", count=10, only_local=False)
    assert len(results) == 1
    assert results[0]["source_path"] == ""


def test_gallery_search_only_scanned(test_db):
    from src.pictova.engine.gallery import gallery_search
    with patch("src.pictova.engine.gallery.get_visual_memory_db_path", return_value=Path(test_db)):
        results = gallery_search("sinop", count=10, only_scanned=True)
    assert len(results) == 1
    assert results[0]["vision_scan_status"] == "done"


def test_gallery_search_location_display(test_db):
    from src.pictova.engine.gallery import gallery_search
    with patch("src.pictova.engine.gallery.get_visual_memory_db_path", return_value=Path(test_db)):
        results = gallery_search("sinop", count=10)
    assert results[0]["location_display"] == "Sinop"


def test_gallery_stats_counts(test_db):
    from src.pictova.engine.gallery import gallery_stats
    with patch("src.pictova.engine.gallery.get_visual_memory_db_path", return_value=Path(test_db)):
        stats = gallery_stats()
    assert stats["total"] == 3
    assert stats["local"] == 2
    assert stats["icloud"] == 1
    assert stats["scanned"] == 1
