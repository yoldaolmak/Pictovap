#!/usr/bin/env python3
"""
Quality comparison and duplicate detection
Perceptual hashing for duplicates, quality scoring for autonomous cleanup
"""
from __future__ import annotations

import json
import hashlib
import sqlite3
from pathlib import Path
from typing import Any
from PIL import Image
import imagehash

from src.core.settings import get_visual_memory_db_path


class PerceptualMatcher:
    """Find similar/duplicate photos using perceptual hashing."""

    @staticmethod
    def compute_phash(image_path: Path) -> str | None:
        """Compute perceptual hash of image."""
        try:
            img = Image.open(image_path)
            return str(imagehash.phash(img))
        except Exception as e:
            print(f"  phash error: {e}")
            return None

    @staticmethod
    def hash_distance(hash1: str, hash2: str) -> int:
        """Hamming distance between two hashes (0-64)."""
        if not hash1 or not hash2:
            return 999
        try:
            h1 = imagehash.ImageHash(bytes.fromhex(hash1))
            h2 = imagehash.ImageHash(bytes.fromhex(hash2))
            return h1 - h2
        except Exception:
            return 999

    @staticmethod
    def are_duplicates(hash1: str, hash2: str, threshold: int = 5) -> bool:
        """Check if hashes indicate duplicates (Hamming distance <= threshold)."""
        return PerceptualMatcher.hash_distance(hash1, hash2) <= threshold

    @staticmethod
    def are_similar(hash1: str, hash2: str, threshold: int = 15) -> bool:
        """Check if hashes indicate similar images (Hamming distance <= threshold)."""
        return PerceptualMatcher.hash_distance(hash1, hash2) <= threshold


class QualityScorer:
    """Score image quality for autonomous cleanup decisions."""

    @staticmethod
    def score_image(image_path: Path) -> dict[str, float]:
        """
        Score image across multiple quality dimensions.

        Returns:
            {
                "sharpness": 0.0-1.0,
                "composition": 0.0-1.0,
                "lighting": 0.0-1.0,
                "color": 0.0-1.0,
                "overall": 0.0-1.0
            }
        """
        try:
            import cv2
            import numpy as np

            img = cv2.imread(str(image_path))
            if img is None:
                return {"error": "Failed to load image"}

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape

            # 1. Sharpness (Laplacian variance)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness_score = min(1.0, laplacian.var() / 500)

            # 2. Composition (edge detection + entropy)
            edges = cv2.Canny(gray, 100, 200)
            edge_density = np.count_nonzero(edges) / (h * w)
            composition_score = min(1.0, edge_density * 2)  # 50% edges = perfect

            # 3. Lighting (histogram spread)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist_spread = np.std(hist)
            lighting_score = min(1.0, hist_spread / 50)  # Higher spread = better

            # 4. Color quality (saturation)
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            saturation = hsv[:, :, 1].mean() / 255.0
            color_score = min(1.0, saturation * 1.2)  # Prefer saturated

            # 5. Overall composite
            overall = (sharpness_score * 0.35 +
                      composition_score * 0.25 +
                      lighting_score * 0.25 +
                      color_score * 0.15)

            return {
                "sharpness": round(float(sharpness_score), 3),
                "composition": round(float(composition_score), 3),
                "lighting": round(float(lighting_score), 3),
                "color": round(float(color_score), 3),
                "overall": round(float(overall), 3),
            }

        except Exception as e:
            return {"error": str(e)}


def find_duplicates_in_hdd(db_path: Path, *, similarity_threshold: int = 5) -> dict[str, list[str]]:
    """
    Find duplicate photos in HDD collection.
    Returns groups of duplicates by phash.
    """
    if not db_path.exists():
        return {}

    conn = sqlite3.connect(db_path)
    conn.execute("ALTER TABLE asset_index ADD COLUMN perceptual_hash TEXT" if True else "")
    conn.row_factory = sqlite3.Row

    # Get all external HDD photos
    rows = conn.execute(
        "SELECT source_id, source_path FROM asset_index WHERE source_type = 'external_hdd' ORDER BY filename"
    ).fetchall()

    print(f"[yo_quality_comparison] Computing hashes for {len(rows)} HDD photos...")

    hash_map: dict[str, str] = {}  # phash -> source_id
    duplicates: dict[str, list[str]] = {}  # group_id -> [source_ids]

    matcher = PerceptualMatcher()

    for row in rows:
        source_id = row["source_id"]
        source_path = Path(row["source_path"])

        if not source_path.exists():
            continue

        phash = matcher.compute_phash(source_path)
        if not phash:
            continue

        # Check against existing hashes
        found_group = False
        for existing_hash, existing_id in list(hash_map.items()):
            if matcher.are_duplicates(phash, existing_hash, threshold=similarity_threshold):
                # Same group
                group_id = existing_hash[:8]
                if group_id not in duplicates:
                    duplicates[group_id] = [existing_id]
                duplicates[group_id].append(source_id)
                found_group = True
                break

        if not found_group:
            hash_map[phash] = source_id

    conn.close()

    return {k: v for k, v in duplicates.items() if len(v) > 1}


def score_duplicate_group(db_path: Path, duplicate_group: list[str]) -> dict[str, Any]:
    """
    Score a group of duplicate photos.
    Returns quality ranking and recommendation (keep/delete).
    """
    if not db_path.exists():
        return {}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    scores: dict[str, dict] = {}
    scorer = QualityScorer()

    for source_id in duplicate_group:
        row = conn.execute(
            "SELECT source_path, filename FROM asset_index WHERE source_id = ?",
            (source_id,),
        ).fetchone()

        if not row:
            continue

        source_path = Path(row["source_path"])
        if not source_path.exists():
            continue

        quality = scorer.score_image(source_path)
        if "error" in quality:
            scores[source_id] = {"quality": 0.0, "filename": row["filename"], "error": quality["error"]}
        else:
            scores[source_id] = {
                "quality": quality.get("overall", 0.0),
                "filename": row["filename"],
                "sharpness": quality.get("sharpness", 0.0),
                "composition": quality.get("composition", 0.0),
                "lighting": quality.get("lighting", 0.0),
                "color": quality.get("color", 0.0),
            }

    conn.close()

    # Sort by quality
    ranked = sorted(scores.items(), key=lambda x: x[1].get("quality", 0.0), reverse=True)

    return {
        "count": len(ranked),
        "best": ranked[0] if ranked else None,
        "worst": ranked[-1] if ranked else None,
        "ranked": ranked,
        "recommendation": {
            "keep": ranked[0][0] if ranked else None,
            "delete": [sid for sid, _ in ranked[1:]] if len(ranked) > 1 else [],
            "reason": "Lowest quality versions should be deleted, highest quality kept",
        },
    }


def compute_hashes_for_db(db_path: Path, *, limit: int = 500):
    """
    Compute perceptual hashes for all HDD photos.
    Store in database for future duplicate detection.
    """
    if not db_path.exists():
        print(f"✗ Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get photos without hashes
    rows = conn.execute(
        """SELECT source_id, source_path, filename
           FROM asset_index
           WHERE source_type = 'external_hdd'
             AND (perceptual_hash IS NULL OR perceptual_hash = '')
           LIMIT ?""",
        (limit,),
    ).fetchall()

    print(f"[yo_quality_comparison] Computing hashes for {len(rows)} photos...")

    matcher = PerceptualMatcher()
    computed = 0

    for i, row in enumerate(rows, 1):
        source_id = row["source_id"]
        source_path = Path(row["source_path"])

        if not source_path.exists():
            print(f"  [{i}] ✗ {row['filename']}: not found")
            continue

        phash = matcher.compute_phash(source_path)
        if phash:
            conn.execute(
                "UPDATE asset_index SET perceptual_hash = ? WHERE source_id = ?",
                (phash, source_id),
            )
            computed += 1
            conn.commit()
            print(f"  [{i}] ✓ {row['filename']}")

        if i % 20 == 0:
            print(f"    → Computed {computed} hashes...")

    conn.close()
    print(f"[yo_quality_comparison] Computed hashes for {computed}/{len(rows)} photos")


if __name__ == "__main__":
    import sys

    DB_PATH = Path(__file__).parent / "data" / "visual_memory.db"

    if len(sys.argv) > 1 and sys.argv[1] == "hashes":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        compute_hashes_for_db(DB_PATH, limit=limit)
    else:
        print("Usage: python3 yo_quality_comparison.py hashes [limit]")
        print("  Computes perceptual hashes for duplicate detection")
