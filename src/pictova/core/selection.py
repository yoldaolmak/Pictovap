#!/usr/bin/env python3
"""
Enhanced semantic search using Claude Vision tags
Searches across scene_ml, objects_json, location_specifics
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from pictova.utils.config import get_visual_memory_db_path


def _ascii_normalize(text: str) -> str:
    """Türkçe → ASCII conversion for path searching."""
    result = str(text or "")
    for src, dst in [
        ("İ", "I"), ("Ş", "S"), ("Ç", "C"), ("Ğ", "G"), ("Ü", "U"), ("Ö", "O"),
        ("ş", "s"), ("ç", "c"), ("ğ", "g"), ("ü", "u"), ("ö", "o"), ("ı", "i"),
    ]:
        result = result.replace(src, dst)
    return result.lower()


def _extract_tags_from_json(json_str: str | None) -> set[str]:
    """Extract tag names from JSON array like [{"tag": "beach", "confidence": 0.9}]."""
    if not json_str:
        return set()
    try:
        data = json.loads(json_str)
        if not isinstance(data, list):
            return set()
        return {item.get("tag", "") for item in data if isinstance(item, dict) and item.get("tag")}
    except (json.JSONDecodeError, TypeError):
        return set()


def search_by_semantic_tags(
    location_query: str,
    count: int,
    semantic_filters: list[str] | None = None,
    min_confidence: float = 0.6,
) -> list[str]:
    """
    Search HDD photos by semantic tags + location path.

    Args:
        location_query: Path-based location (e.g., "madura adası", "alaçatı")
        count: Number of results
        semantic_filters: List of semantic tags to match (e.g., ["beach", "sunset", "people"])
        min_confidence: Minimum tag confidence (0-1)

    Returns:
        List of matching file paths
    """
    db_path = get_visual_memory_db_path()
    if not db_path.exists():
        return []

    # Parse location query into path tokens
    normalized = _ascii_normalize(location_query)
    tokens = [t for t in re.split(r"\s+", normalized) if len(t) >= 3]
    if not tokens:
        return []

    # Build location WHERE clause (all tokens must match in path)
    like_parts = [f"LOWER(source_path) LIKE '%{t}%'" for t in tokens]
    location_where = " AND ".join(like_parts)

    # Build semantic filter SQL
    tag_conditions = []
    if semantic_filters:
        for filter_tag in semantic_filters:
            # Match tag in scene_ml, objects_json, location_specifics, or time_of_day
            tag_sql = f"""
                (scene_ml LIKE '%"{filter_tag}"%'
                 OR objects_json LIKE '%"{filter_tag}"%'
                 OR time_of_day LIKE '%"{filter_tag}"%'
                 OR location_specifics LIKE '%"{filter_tag}"%')
            """
            tag_conditions.append(tag_sql)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        where = f"({location_where}) AND is_personal = 0"
        if tag_conditions:
            # Match ANY of the semantic filters (OR logic)
            where += f" AND ({' OR '.join(tag_conditions)})"

        sql = f"""
            SELECT source_path, filename, quality_score, selection_score,
                   scene_ml, objects_json, location_specifics
            FROM asset_index
            WHERE source_type = 'external_hdd'
              AND {where}
            ORDER BY selection_score DESC, quality_score DESC
            LIMIT ?
        """

        rows = conn.execute(sql, [count * 3]).fetchall()

    finally:
        conn.close()

    # Return file paths (verified to exist)
    paths = []
    for row in rows:
        p = Path(row["source_path"])
        if p.exists():
            paths.append(str(p))
        if len(paths) >= count:
            break

    return paths


def search_with_all_semantic_tags(
    location_query: str,
    count: int,
    required_tags: list[str],
    optional_tags: list[str] | None = None,
) -> list[str]:
    """
    Search with required + optional semantic tags.

    Args:
        location_query: Path-based location
        count: Number of results
        required_tags: All must match (AND logic)
        optional_tags: At least one should match (OR logic)

    Returns:
        List of matching file paths
    """
    db_path = get_visual_memory_db_path()
    if not db_path.exists():
        return []

    # Parse location
    normalized = _ascii_normalize(location_query)
    tokens = [t for t in re.split(r"\s+", normalized) if len(t) >= 3]
    location_where = " AND ".join([f"LOWER(source_path) LIKE '%{t}%'" for t in tokens])

    # Required tags (all must match)
    required_conditions = []
    for tag in required_tags:
        tag_sql = f"""
            (scene_ml LIKE '%"{tag}"%'
             OR objects_json LIKE '%"{tag}"%'
             OR time_of_day LIKE '%"{tag}"%'
             OR location_specifics LIKE '%"{tag}"%')
        """
        required_conditions.append(tag_sql)

    # Optional tags (at least one)
    optional_sql = ""
    if optional_tags:
        optional_conditions = []
        for tag in optional_tags:
            tag_sql = f"""
                (scene_ml LIKE '%"{tag}"%'
                 OR objects_json LIKE '%"{tag}"%'
                 OR time_of_day LIKE '%"{tag}"%'
                 OR location_specifics LIKE '%"{tag}"%')
            """
            optional_conditions.append(tag_sql)
        optional_sql = f" OR ({' OR '.join(optional_conditions)})"

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        where = f"({location_where}) AND is_personal = 0"
        if required_conditions:
            where += f" AND ({' AND '.join(required_conditions)})"
        if optional_sql:
            where += optional_sql

        sql = f"""
            SELECT source_path, filename, quality_score, selection_score
            FROM asset_index
            WHERE source_type = 'external_hdd'
              AND {where}
            ORDER BY selection_score DESC, quality_score DESC
            LIMIT ?
        """

        rows = conn.execute(sql, [count * 3]).fetchall()

    finally:
        conn.close()

    paths = []
    for row in rows:
        p = Path(row["source_path"])
        if p.exists():
            paths.append(str(p))
        if len(paths) >= count:
            break

    return paths


def get_tag_suggestions(location_query: str, limit: int = 10) -> dict[str, list[str]]:
    """
    Get the most common semantic tags for a location.
    Useful for understanding what's available before searching.
    """
    db_path = get_visual_memory_db_path()
    if not db_path.exists():
        return {}

    normalized = _ascii_normalize(location_query)
    tokens = [t for t in re.split(r"\s+", normalized) if len(t) >= 3]
    if not tokens:
        return {}

    like_parts = [f"LOWER(source_path) LIKE '%{t}%'" for t in tokens]
    location_where = " AND ".join(like_parts)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        sql = f"""
            SELECT scene_ml, objects_json, location_specifics
            FROM asset_index
            WHERE source_type = 'external_hdd'
              AND is_personal = 0
              AND ({location_where})
        """

        rows = conn.execute(sql).fetchall()

    finally:
        conn.close()

    # Aggregate all tags
    all_tags: dict[str, int] = {}

    for row in rows:
        for field in ["scene_ml", "objects_json"]:
            tags = _extract_tags_from_json(row[field])
            for tag in tags:
                all_tags[tag] = all_tags.get(tag, 0) + 1

        # Parse location_specifics
        loc_spec = row["location_specifics"]
        if loc_spec:
            try:
                loc_data = json.loads(loc_spec)
                for category, items in loc_data.items():
                    if isinstance(items, list):
                        for item in items:
                            tag = item.get("tag") if isinstance(item, dict) else str(item)
                            if tag:
                                all_tags[tag] = all_tags.get(tag, 0) + 1
            except (json.JSONDecodeError, TypeError):
                pass

    # Return top tags by frequency
    sorted_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)
    return {"available_tags": [tag for tag, _ in sorted_tags[:limit]]}


if __name__ == "__main__":
    # Example usage
    print("=== Tag Suggestions for 'alaçatı' ===")
    suggestions = get_tag_suggestions("alaçatı")
    print(json.dumps(suggestions, indent=2, ensure_ascii=False))

    print("\n=== Search: Alaçatı + beach + sunset ===")
    paths = search_by_semantic_tags("alaçatı", count=5, semantic_filters=["beach", "sunset"])
    for p in paths:
        print(f"  {Path(p).name}")

    print("\n=== Search: Madura + required [island, ocean] + optional [people] ===")
    paths = search_with_all_semantic_tags(
        "madura adası",
        count=3,
        required_tags=["island", "ocean"],
        optional_tags=["people", "boat"]
    )
    for p in paths:
        print(f"  {Path(p).name}")
