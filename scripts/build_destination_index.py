#!/usr/bin/env python3
"""Her destinasyon için en iyi photosların UUID önbelleği.

visual_memory.db → destination_index.json
Format: {"Sinop": ["uuid1","uuid2",...], "Antalya": [...], ...}

Bu indeks iCloud indirme önceliğini belirler.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get(
    "YO_VISUAL_MEMORY_DB",
    "/Users/yoldaolmak/Projects/Pictova/data/visual_memory.db",
))
OUT_PATH = DB_PATH.parent / "destination_index.json"
TOP_N = 20  # Her destinasyondan en iyi N foto


def main():
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row

    # Tüm benzersiz destinasyonlar
    locs = con.execute("""
        SELECT DISTINCT COALESCE(city, state_province) AS loc, COUNT(*) AS cnt
        FROM asset_index
        WHERE is_personal = 0
          AND COALESCE(city, state_province) IS NOT NULL
          AND COALESCE(city, state_province) != ''
        GROUP BY loc
        ORDER BY cnt DESC
    """).fetchall()

    index: dict[str, list[str]] = {}
    for loc_row in locs:
        loc = loc_row["loc"]
        rows = con.execute("""
            SELECT source_id
            FROM asset_index
            WHERE is_personal = 0
              AND (city = ? OR state_province = ?)
            ORDER BY
              (CASE WHEN vision_scan_status = 'done' THEN 1 ELSE 0 END) DESC,
              quality_score DESC,
              selection_score DESC
            LIMIT ?
        """, [loc, loc, TOP_N]).fetchall()
        if rows:
            index[loc] = [r["source_id"] for r in rows]

    con.close()

    OUT_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ {len(index)} destinasyon → {OUT_PATH}")
    # Özet
    top = sorted(index.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for name, uuids in top:
        print(f"   {name:<28} {len(uuids)} foto")


if __name__ == "__main__":
    main()
