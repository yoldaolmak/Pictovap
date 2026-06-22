"""Gallery motor — Visual Memory DB'den arama ve seçim."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.media_publish import (
    build_publish_slug_candidates,
    embed_metadata,
    ensure_publish_path,
    ensure_unique_slug,
)
from src.pictova.config import get_visual_memory_db_path


def gallery_search(
    query: str,
    *,
    count: int = 10,
    only_local: bool = True,
    only_scanned: bool = False,
    city: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Visual Memory DB'de fotoğraf ara. Dict listesi döner."""
    db_path = str(get_visual_memory_db_path())
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    conditions = ["a.is_personal = 0"]
    params: list[Any] = []

    if only_local:
        conditions.append("a.source_path != ''")

    if only_scanned:
        conditions.append("a.vision_scan_status = 'done'")

    if city:
        conditions.append("(LOWER(a.city) = LOWER(?) OR LOWER(a.state_province) = LOWER(?))")
        params.extend([city, city])

    rows: list = []
    try:
        fts_q = " ".join(f'"{w}"*' for w in query.lower().split() if len(w) >= 2) or '""'
        fts_sql = f"""
            SELECT a.source_id, a.source_path, a.filename, a.city, a.state_province,
                   a.country, a.quality_score, a.selection_score, a.orientation,
                   a.scene, a.activity, a.summary, a.ai_keywords_json,
                   a.vision_scan_status, a.latitude, a.longitude
            FROM asset_search s
            JOIN asset_index a ON a.source_id = s.source_id
            WHERE s.document MATCH ?
              AND {' AND '.join(conditions)}
            ORDER BY
              (CASE WHEN a.vision_scan_status = 'done' THEN 1 ELSE 0 END) DESC,
              a.quality_score DESC
            LIMIT ?
        """
        rows = con.execute(fts_sql, [fts_q, *params, count * 2]).fetchall()
    except Exception:
        pass

    # Yeterli değilse LIKE fallback
    if len(rows) < count:
        like_val = f"%{query.lower()}%"
        seen_ids = {r["source_id"] for r in rows}
        # LIKE fallback: conditions'daki "a." prefix'leri kaldır
        like_conditions = [c.replace("a.is_personal", "is_personal")
                            .replace("a.source_path", "source_path")
                            .replace("a.vision_scan_status", "vision_scan_status")
                            .replace("a.city", "city")
                            .replace("a.state_province", "state_province")
                           for c in conditions]
        like_cond = " AND ".join(like_conditions + [
            "(LOWER(COALESCE(city,'')) LIKE ? OR LOWER(COALESCE(state_province,'')) LIKE ? "
            "OR LOWER(COALESCE(summary,'')) LIKE ?)"
        ])
        fb = con.execute(f"""
            SELECT source_id, source_path, filename, city, state_province, country,
                   quality_score, selection_score, orientation, scene, activity, summary,
                   ai_keywords_json, vision_scan_status, latitude, longitude
            FROM asset_index
            WHERE {like_cond}
            ORDER BY quality_score DESC
            LIMIT ?
        """, [*params, like_val, like_val, like_val, count]).fetchall()
        rows = list(rows) + [r for r in fb if r["source_id"] not in seen_ids]

    con.close()
    results = []
    for r in rows[:count]:
        d = dict(r)
        d["location_display"] = d.get("city") or d.get("state_province") or d.get("country") or ""
        results.append(d)
    return results


def gallery_stats() -> Dict[str, Any]:
    """Kısa istatistik özeti."""
    db_path = str(get_visual_memory_db_path())
    con = sqlite3.connect(db_path)
    row = con.execute("""
        SELECT
          COUNT(*) AS total,
          SUM(CASE WHEN source_path != '' THEN 1 ELSE 0 END) AS local_count,
          SUM(CASE WHEN source_path  = '' THEN 1 ELSE 0 END) AS icloud_count,
          SUM(CASE WHEN vision_scan_status = 'done' THEN 1 ELSE 0 END) AS scanned,
          COUNT(DISTINCT COALESCE(city, state_province)) AS unique_locations
        FROM asset_index WHERE is_personal = 0
    """).fetchone()
    con.close()
    return {
        "total": row[0],
        "local": row[1],
        "icloud": row[2],
        "scanned": row[3],
        "unique_locations": row[4],
    }


__all__ = [
    "build_publish_slug_candidates",
    "embed_metadata",
    "ensure_publish_path",
    "ensure_unique_slug",
    "gallery_search",
    "gallery_stats",
]
