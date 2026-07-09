#!/usr/bin/env python3
"""UUID cache of the best photos for each destination.

visual_memory.db → destination_index.json
Format: {"Sinop": ["uuid1","uuid2",...], "Antalya": [...], ...}

This index determines the iCloud download priority.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get(
    "YO_VISUAL_MEMORY_DB",
    "/Users/yoldaolmak/Projects/Pictovap/data/visual_memory.db",
))
OUT_PATH = DB_PATH.parent / "destination_index.json"
TOP_N = 20  # Top N photos from each destination


def main():
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row

    # All unique destinations
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
    print(f"✅ {len(index)} destinations → {OUT_PATH}")
    # Summary
    top = sorted(index.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for name, uuids in top:
        print(f"   {name:<28} {len(uuids)} photos")


if __name__ == "__main__":
    main()
