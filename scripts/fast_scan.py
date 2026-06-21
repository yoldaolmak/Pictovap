#!/usr/bin/env python3
"""Paralel vision scan — birden fazla Claude CLI süreci eşzamanlı çalıştırır.

Kullanım:
  python3 scripts/fast_scan.py --workers 3 --limit 120
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pictova.engine.vision_chain import analyze_image_vision_chain, has_any_vision_source

DB_PATH = Path(os.environ.get(
    "YO_VISUAL_MEMORY_DB",
    "/Users/yoldaolmak/Downloads/YO_OS_VIL/data/visual_memory.db",
))

_lock = threading.Lock()
_done = 0
_errors = 0
_total = 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _update_done(con_path: str, source_id: str, result: dict) -> None:
    kws = result.get("keywords") or []
    con = sqlite3.connect(con_path)
    con.execute("""
        UPDATE asset_index SET
            ai_keywords_json = ?,
            scene = ?,
            activity = ?,
            summary = ?,
            vision_scan_status = 'done',
            vision_last_scanned_at = ?,
            vision_last_error = NULL
        WHERE source_id = ?
    """, [
        json.dumps(kws, ensure_ascii=False),
        result.get("scene", ""),
        result.get("activity", ""),
        result.get("alt") or result.get("caption") or "",
        _now(),
        source_id,
    ])
    con.commit()
    con.close()


def _update_error(con_path: str, source_id: str, error: str) -> None:
    con = sqlite3.connect(con_path)
    con.execute("""
        UPDATE asset_index SET
            vision_scan_status = 'error',
            vision_last_error = ?,
            vision_last_scanned_at = ?
        WHERE source_id = ?
    """, [error[:500], _now(), source_id])
    con.commit()
    con.close()


def _worker(rows: list, db_str: str, idx: int) -> None:
    global _done, _errors
    for row in rows:
        src = row[1]
        uid = row[0]
        city = row[2] or row[3] or row[4] or ""
        if not Path(src).exists():
            _update_error(db_str, uid, "file_not_found")
            with _lock:
                _errors += 1
                print(f"  ✗ [{idx}] {Path(src).name}: dosya yok")
            continue
        post_ctx = {"title": city, "slug": city.lower().replace(" ", "-")}
        try:
            result = analyze_image_vision_chain(src, location_hint=city, post_context=post_ctx)
            _update_done(db_str, uid, result)
            with _lock:
                _done += 1
                pct = int(_done / _total * 100) if _total else 0
                print(f"  ✓ [{idx}] {Path(src).name} ({result.get('source','?')}) {pct}% → {result.get('keywords',[])[:3]}")
        except RuntimeError as exc:
            _update_error(db_str, uid, str(exc))
            with _lock:
                _errors += 1
                print(f"  ✗ [{idx}] {Path(src).name}: {str(exc)[:120]}", file=sys.stderr)


def main():
    global _total
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    if not has_any_vision_source():
        print("❌ Vision kaynağı yok.", file=sys.stderr)
        sys.exit(1)

    con = sqlite3.connect(str(DB_PATH))
    q = """
        SELECT source_id, source_path, city, state_province, country
        FROM asset_index
        WHERE vision_scan_status = 'pending'
          AND source_path != '' AND source_path IS NOT NULL
        ORDER BY quality_score DESC
    """
    if args.limit:
        q += f" LIMIT {args.limit}"
    rows = con.execute(q).fetchall()
    con.close()

    _total = len(rows)
    print(f"🔍 {_total} fotoğraf → {args.workers} paralel worker")

    # Satırları worker'lara böl (round-robin)
    buckets: list[list] = [[] for _ in range(args.workers)]
    for i, row in enumerate(rows):
        buckets[i % args.workers].append(row)

    db_str = str(DB_PATH)
    threads = [
        threading.Thread(target=_worker, args=(buckets[i], db_str, i + 1), daemon=True)
        for i in range(args.workers)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"\n✅ Tamamlandı: {_done} başarılı, {_errors} hata")


if __name__ == "__main__":
    main()
