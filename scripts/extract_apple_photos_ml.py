#!/usr/bin/env python3
"""
Extract Apple Photos ML metadata (blur, exposure, face count) to visual_memory.db
Maps ZMEDIAANALYSISASSETATTRIBUTES to asset_index by filename matching.
"""
from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from datetime import datetime

PHOTOS_DB = Path("~/Pictures/Photos Library.photoslibrary/database/Photos.sqlite").expanduser()
VISUAL_DB = Path(__file__).parent / "data" / "visual_memory.db"

def normalize_blur_exposure(blur_score: float, exposure_score: float) -> float:
    """Combine blur and exposure into a single quality metric (0-1)"""
    # Blur: lower is better (1.0 = sharp, 0.0 = blurry)
    # Exposure: center is best (0.5 optimal, 0.0 = dark, 1.0 = bright)
    blur_quality = 1.0 - min(1.0, blur_score)  # Invert so high = good
    exposure_quality = 1.0 - abs(exposure_score - 0.5) * 2  # Peak at 0.5
    return (blur_quality * 0.6 + exposure_quality * 0.4)

def main():
    if not PHOTOS_DB.exists():
        print(f"✗ Photos DB not found: {PHOTOS_DB}")
        return
    if not VISUAL_DB.exists():
        print(f"✗ Visual memory DB not found: {VISUAL_DB}")
        return

    print(f"[extract_apple_photos_ml] START")

    photos_conn = sqlite3.connect(PHOTOS_DB)
    photos_conn.row_factory = sqlite3.Row
    visual_conn = sqlite3.connect(VISUAL_DB)
    visual_conn.row_factory = sqlite3.Row

    # Query Photos.sqlite for ML metadata
    sql = """
    SELECT
        a.ZUUID,
        a.ZFILENAME AS filename,
        maa.ZBLURRINESSSCORE,
        maa.ZEXPOSURESCORE,
        maa.ZFACECOUNT
    FROM ZASSET a
    LEFT JOIN ZMEDIAANALYSISASSETATTRIBUTES maa ON maa.ZASSET = a.Z_PK
    WHERE maa.ZBLURRINESSSCORE IS NOT NULL OR maa.ZFACECOUNT IS NOT NULL OR maa.ZEXPOSURESCORE IS NOT NULL
    """

    try:
        photos_rows = photos_conn.execute(sql).fetchall()
    except sqlite3.OperationalError as e:
        print(f"✗ SQL error (columns might not exist on older Photos versions): {e}")
        photos_conn.close()
        visual_conn.close()
        return

    print(f"  Found {len(photos_rows)} rows with ML metadata in Photos DB")

    # Match by filename and update visual_memory.db
    updated = 0
    for row in photos_rows:
        filename = row["filename"] or ""
        if not filename:
            continue

        # Extract data
        blur_score = float(row["ZBLURRINESSSCORE"] or 0)
        exposure_score = float(row["ZEXPOSURESCORE"] or 0)
        face_count = int(row["ZFACECOUNT"] or 0)

        # Calculate quality score from Apple ML metrics
        combined_quality = normalize_blur_exposure(blur_score, exposure_score)

        # Build person object if faces detected
        person_objects = []
        if face_count >= 1:
            person_objects = [{"name": "person", "confidence": 0.9}] * min(face_count, 5)

        # Update asset_index
        visual_conn.execute("""
            UPDATE asset_index
            SET
                quality_score = MAX(quality_score, ?),
                objects_json = CASE
                    WHEN ? > 0 THEN json(?)
                    ELSE objects_json
                END,
                apple_blur_score = ?,
                apple_exposure_score = ?
            WHERE LOWER(filename) = LOWER(?)
        """, (
            combined_quality,
            face_count,
            json.dumps(person_objects),
            blur_score,
            exposure_score,
            filename,
        ))
        updated += visual_conn.total_changes

    visual_conn.commit()
    print(f"  Updated {updated} asset_index rows with Apple ML metadata")

    photos_conn.close()
    visual_conn.close()
    print(f"[extract_apple_photos_ml] DONE")

if __name__ == "__main__":
    main()
