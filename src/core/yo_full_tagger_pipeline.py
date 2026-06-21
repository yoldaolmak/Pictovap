#!/usr/bin/env python3
"""
Full semantic tagging pipeline coordinator
Orchestrates Claude Vision tagging → face detection → quality scoring
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from datetime import datetime
import time

from src.core.settings import get_visual_memory_db_path


class FullTaggerPipeline:
    """Coordinated semantic tagging: Vision → Faces → Quality → DB"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def get_tagging_stats(self) -> dict[str, Any]:
        """Get current tagging progress."""
        stats = {}

        # Overall progress
        total = self.conn.execute(
            "SELECT COUNT(*) as c FROM asset_index WHERE source_type = 'external_hdd'"
        ).fetchone()["c"]

        fully_tagged = self.conn.execute(
            """SELECT COUNT(*) as c FROM asset_index
               WHERE source_type = 'external_hdd'
                 AND scene_ml IS NOT NULL AND scene_ml != ''
                 AND objects_json IS NOT NULL AND objects_json != ''
                 AND location_specifics IS NOT NULL AND location_specifics != ''"""
        ).fetchone()["c"]

        vision_only = self.conn.execute(
            """SELECT COUNT(*) as c FROM asset_index
               WHERE source_type = 'external_hdd'
                 AND scene_ml IS NOT NULL AND scene_ml != ''"""
        ).fetchone()["c"]

        try:
            with_hashes = self.conn.execute(
                """SELECT COUNT(*) as c FROM asset_index
                   WHERE source_type = 'external_hdd'
                     AND perceptual_hash IS NOT NULL AND perceptual_hash != ''"""
            ).fetchone()["c"]
        except sqlite3.OperationalError:
            with_hashes = 0

        stats["total_photos"] = total
        stats["fully_tagged"] = fully_tagged
        stats["vision_tagged"] = vision_only
        stats["with_perceptual_hash"] = with_hashes
        stats["progress_percent"] = round(100 * vision_only / max(1, total), 1)
        stats["estimated_remaining_time_hours"] = round((total - vision_only) / 10, 1)  # ~10/min

        return stats

    def print_progress(self):
        """Print tagging progress report."""
        stats = self.get_tagging_stats()

        print("\n" + "="*60)
        print(f"  TAGGING PROGRESS REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        print(f"  Total HDD photos:           {stats['total_photos']}")
        print(f"  Claude Vision tagged:       {stats['vision_tagged']} ({stats['progress_percent']}%)")
        print(f"  Fully tagged (Vision+Face): {stats['fully_tagged']}")
        print(f"  With perceptual hash:       {stats['with_perceptual_hash']}")
        print(f"  Est. remaining time:        {stats['estimated_remaining_time_hours']}h (at ~10/min)")
        print("="*60 + "\n")

        return stats

    def print_sample_tags(self, limit: int = 5):
        """Print sample of tagged photos."""
        rows = self.conn.execute(
            """SELECT filename, scene_ml, objects_json, location_specifics
               FROM asset_index
               WHERE source_type = 'external_hdd'
                 AND scene_ml IS NOT NULL AND scene_ml != ''
               LIMIT ?""",
            (limit,),
        ).fetchall()

        if not rows:
            print("  No tagged photos yet")
            return

        print(f"\n  Sample {len(rows)} tagged photos:\n")
        for row in rows:
            print(f"    {row['filename']}")
            if row['scene_ml']:
                scenes = json.loads(row['scene_ml'])
                scene_tags = [f"{s['tag']}" for s in scenes[:2]]
                print(f"      Scenes: {', '.join(scene_tags)}")

            if row['objects_json']:
                objects = json.loads(row['objects_json'])
                obj_tags = [f"{o.get('name', o.get('tag', str(o)))}" for o in objects[:3] if isinstance(o, dict)]
                print(f"      Objects: {', '.join(obj_tags)}")

            if row['location_specifics']:
                try:
                    loc = json.loads(row['location_specifics'])
                    if loc.get('description'):
                        print(f"      Description: {loc['description']}")
                except (json.JSONDecodeError, TypeError):
                    pass
            print()

    def get_tagging_queue(self) -> list[dict[str, Any]]:
        """Get list of photos waiting for tagging."""
        rows = self.conn.execute(
            """SELECT source_id, filename, quality_score, selection_score
               FROM asset_index
               WHERE source_type = 'external_hdd'
                 AND (scene_ml IS NULL OR scene_ml = '')
                 AND is_personal = 0
               ORDER BY quality_score DESC, selection_score DESC
               LIMIT 50"""
        ).fetchall()

        return [dict(row) for row in rows]

    def estimate_completion_time(self) -> str:
        """Estimate when all photos will be tagged."""
        stats = self.get_tagging_stats()
        remaining = stats["total_photos"] - stats["vision_tagged"]

        # Assume 10 photos/minute with Claude API
        minutes = remaining / 10
        hours = minutes / 60

        if hours < 1:
            return f"{int(minutes)} minutes"
        elif hours < 24:
            return f"{hours:.1f} hours"
        else:
            days = hours / 24
            return f"{days:.1f} days"

    def close(self):
        """Close database connection."""
        self.conn.close()


def main():
    """Print tagging status and recommendations."""
    db_path = get_visual_memory_db_path()
    if not db_path.exists():
        print("✗ Database not found")
        return

    pipeline = FullTaggerPipeline(db_path)

    # Print progress
    stats = pipeline.print_progress()

    # Print samples
    pipeline.print_sample_tags(limit=3)

    # Recommendations
    print("  NEXT STEPS:")
    print(f"    1. Semantic tagging in progress (~{pipeline.estimate_completion_time()} remaining)")
    print("    2. After Vision tagging → run face detection:")
    print("       python3 yo_face_detector.py 600")
    print("    3. Compute perceptual hashes for duplicates:")
    print("       python3 yo_quality_comparison.py hashes 600")
    print("    4. Test semantic search:")
    print("       python3 -c \"from yo_semantic_search import search_with_all_semantic_tags; ")
    print("       paths = search_with_all_semantic_tags('madura', 5, ['island'], ['ocean']);")
    print("       print(f'Found {len(paths)} photos')\"")
    print("\n")

    # Queue preview
    queue = pipeline.get_tagging_queue()
    if queue:
        print(f"  TAGGING QUEUE ({len(queue)} pending):")
        for i, item in enumerate(queue[:5], 1):
            print(f"    {i}. {item['filename']} (quality={item['quality_score']:.2f})")
        if len(queue) > 5:
            print(f"    ... and {len(queue) - 5} more")
        print()

    pipeline.close()


if __name__ == "__main__":
    main()
