#!/usr/bin/env python3
"""Pictova — Bulk vision scan for local photos.

Processes only records where source_path is filled (locally available) and vision_scan_status='pending'.
Fills ai_keywords, scene, and activity fields using the Vision chain (Gemini→Codex→Claude).
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pictova.engine.vision_chain import analyze_image_vision_chain, has_any_vision_source

DB_PATH = Path(os.environ.get(
    "YO_VISUAL_MEMORY_DB",
    "/Users/yoldaolmak/Projects/Pictova/data/visual_memory.db",
))

UPDATE_SQL = """
UPDATE asset_index SET
    ai_keywords_json     = :ai_keywords_json,
    scene                = :scene,
    activity             = :activity,
    summary              = :summary,
    people_json          = :people_json,
    vision_scan_status   = 'done',
    vision_last_scanned_at = :scanned_at,
    vision_last_error    = NULL
WHERE source_id = :source_id
"""

ERROR_SQL = """
UPDATE asset_index SET
    vision_scan_status = 'error',
    vision_last_error  = :error,
    vision_last_scanned_at = :scanned_at
WHERE source_id = :source_id
"""


def _extract_scene_activity(keywords: list[str]) -> tuple[str, str]:
    """Estimate scene and activity from keyword list."""
    scene_words = {"coast", "beach", "mountain", "forest", "city", "urban", "rural",
                   "sea", "lake", "river", "valley", "castle", "mosque", "church",
                   "market", "bazaar", "harbor", "port", "ruins", "landscape", "nature"}
    activity_words = {"walking", "hiking", "swimming", "sailing", "photography",
                      "tourism", "travel", "dining", "shopping", "sightseeing"}
    kw_lower = {k.lower() for k in keywords}
    scene = next((w for w in kw_lower if w in scene_words), "general")
    activity = next((w for w in kw_lower if w in activity_words), "travel")
    return scene, activity


def main():
    if not has_any_vision_source():
        print("❌ No Vision source. Add GEMINI_API_KEY or open a codex/claude session.", file=sys.stderr)
        sys.exit(1)

    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row

    rows = con.execute("""
        SELECT source_id, source_path, city, state_province, country, filename
        FROM asset_index
        WHERE vision_scan_status = 'pending'
          AND source_path != ''
          AND source_path IS NOT NULL
        ORDER BY quality_score DESC
    """).fetchall()

    total = len(rows)
    print(f"🔍 {total} local photos awaiting vision scan")

    if total == 0:
        print("✅ All scanned.")
        con.close()
        return

    done = errors = 0
    for i, row in enumerate(rows):
        src = row["source_path"]
        uid = row["source_id"]
        city = row["city"] or row["state_province"] or row["country"] or ""

        # Is the file still available?
        if not Path(src).exists():
            con.execute(ERROR_SQL, {
                "source_id": uid,
                "error": "file_not_found",
                "scanned_at": _now(),
            })
            con.commit()
            errors += 1
            continue

        post_ctx = {"title": city, "slug": city.lower().replace(" ", "-")}
        try:
            result = analyze_image_vision_chain(
                src,
                location_hint=city,
                post_context=post_ctx,
            )
        except RuntimeError as exc:
            con.execute(ERROR_SQL, {
                "source_id": uid,
                "error": str(exc)[:500],
                "scanned_at": _now(),
            })
            con.commit()
            errors += 1
            print(f"  ✗ [{i+1}/{total}] {row['filename']}: {exc}", file=sys.stderr)
            continue

        keywords = result.get("keywords") or []
        people = result.get("people") or []
        alt = result.get("alt") or ""
        caption = result.get("caption") or ""
        scene = result.get("scene") or ""
        activity = result.get("activity") or ""
        if not scene or not activity:
            scene_f, activity_f = _extract_scene_activity(keywords)
            scene = scene or scene_f
            activity = activity or activity_f
        summary = alt or caption

        con.execute(UPDATE_SQL, {
            "source_id": uid,
            "ai_keywords_json": json.dumps(keywords, ensure_ascii=False),
            "scene": scene,
            "activity": activity,
            "summary": summary,
            "people_json": json.dumps(people, ensure_ascii=False),
            "scanned_at": _now(),
        })
        con.commit()
        done += 1

        source = result.get("source", "?")
        print(f"  ✓ [{i+1}/{total}] {row['filename']} ({source}) → {keywords[:4]}")

        # Codex is slow — no rate limit but let's wait a bit
        if source == "codex_cli":
            time.sleep(2)

    con.close()
    print(f"\n✅ Completed: {done} scanned, {errors} errors")

    if done > 0:
        print("\n🔄 Rebuilding FTS index...")
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location(
            "rebuild_fts",
            str(Path(__file__).parent / "rebuild_fts.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
