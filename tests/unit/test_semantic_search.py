from __future__ import annotations

from pictova import main


def _row(source_id: str, *, created_at: str, latitude: float, longitude: float) -> dict:
    return {
        "source_id": source_id,
        "source_path": f"/{source_id}.jpg",
        "created_at": created_at,
        "latitude": latitude,
        "longitude": longitude,
        "people_json": "[]",
        "apple_labels_json": "[]",
    }


def test_select_diverse_rows_suppresses_capture_bursts(monkeypatch):
    monkeypatch.setattr(main.Path, "exists", lambda _path: False)
    rows = [
        _row("burst-a", created_at="2026-06-17T13:27:18+03:00", latitude=38.6476, longitude=26.5119),
        _row("burst-b", created_at="2026-06-17T13:27:40+03:00", latitude=38.6477, longitude=26.5118),
        _row("later", created_at="2026-06-17T15:30:00+03:00", latitude=38.6477, longitude=26.5118),
    ]

    selected = main._select_diverse_rows(rows, 3)

    assert [row["source_id"] for row in selected] == ["burst-a", "later"]


def test_select_diverse_rows_suppresses_visual_near_duplicates(monkeypatch):
    monkeypatch.setattr(main.Path, "exists", lambda _path: True)
    hashes = {"/same-a.jpg": 0, "/same-b.jpg": 3, "/different.jpg": (1 << 64) - 1}
    monkeypatch.setattr(main, "_perceptual_hash", lambda path: hashes[path])
    rows = [
        _row("same-a", created_at="2026-06-17T10:00:00+03:00", latitude=38.60, longitude=26.50),
        _row("same-b", created_at="2026-06-18T10:00:00+03:00", latitude=38.61, longitude=26.51),
        _row("different", created_at="2026-06-19T10:00:00+03:00", latitude=38.62, longitude=26.52),
    ]

    selected = main._select_diverse_rows(rows, 3)

    assert [row["source_id"] for row in selected] == ["same-a", "different"]


def test_hero_score_reads_sqlite_style_rows_without_get():
    class Row:
        def __init__(self, values):
            self.values = values

        def __getitem__(self, key):
            return self.values[key]

    row = Row({
        "quality_score": 0.9,
        "filename": "",
        "title": "",
        "description": "",
        "location": "",
        "activity": "travel",
        "summary": "",
        "ai_keywords_json": '["karaburun", "ege denizi"]',
        "orientation": "landscape",
        "scene": "coast",
    })

    assert main._hero_score(row, {"title": "Karaburun Gezi Rehberi", "slug": ""}) > 3


def test_select_diverse_rows_excludes_people_unless_requested(monkeypatch):
    monkeypatch.setattr(main.Path, "exists", lambda _path: False)
    person = _row("person", created_at="2026-06-17T10:00:00+03:00", latitude=38.60, longitude=26.50)
    person["people_json"] = '["Known Person"]'
    coast = _row("coast", created_at="2026-06-17T11:00:00+03:00", latitude=38.61, longitude=26.51)

    assert [row["source_id"] for row in main._select_diverse_rows([person, coast], 2)] == ["coast"]
    assert [
        row["source_id"]
        for row in main._select_diverse_rows([person, coast], 2, allow_people=True)
    ] == ["person", "coast"]
