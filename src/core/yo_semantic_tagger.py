#!/usr/bin/env python3
"""
Semantic Tagger for HDD photos using Claude Vision
Comprehensive tag taxonomy (Depositphotos-style) with confidence scores
"""
from __future__ import annotations

import json
import base64
import sqlite3
from pathlib import Path
from typing import Any
import anthropic
from PIL import Image
import io

# Comprehensive tag taxonomy (Depositphotos-aligned)
TAG_CATEGORIES = {
    "scene_type": [
        "landscape", "portrait", "architecture", "nature", "wildlife",
        "macro", "street", "aerial", "underwater", "panoramic",
        "still_life", "food", "interior", "exterior", "abstract"
    ],
    "objects": [
        "people", "person", "woman", "man", "child", "elderly",
        "animals", "dog", "cat", "bird", "horse", "wildlife",
        "buildings", "house", "church", "temple", "skyscraper",
        "vehicles", "car", "bicycle", "boat", "airplane",
        "nature", "tree", "flower", "water", "mountain", "beach", "forest",
        "food", "fruit", "vegetable", "meal", "drink",
        "objects", "book", "computer", "phone", "furniture",
        "sky", "clouds", "sunset", "sunrise", "snow", "rain"
    ],
    "activity": [
        "travel", "tourism", "hiking", "walking", "running",
        "sports", "playing", "swimming", "cycling", "skiing",
        "working", "studying", "reading", "writing", "cooking",
        "socializing", "gathering", "party", "celebration", "wedding",
        "business", "meeting", "conference", "presentation",
        "relaxation", "meditation", "yoga", "exercise"
    ],
    "location_type": [
        "urban", "city", "street", "marketplace", "downtown",
        "rural", "countryside", "village", "farmland",
        "beach", "coast", "seaside", "bay", "harbor",
        "mountain", "hill", "valley", "alpine", "summit",
        "forest", "woodland", "jungle", "garden", "park",
        "water", "lake", "river", "stream", "pond",
        "desert", "island", "tropical", "temperate", "arctic",
        "indoor", "home", "office", "restaurant", "museum",
        "temple", "mosque", "church", "historical_site", "landmark"
    ],
    "time_of_day": [
        "daytime", "morning", "midday", "noon", "afternoon",
        "golden_hour", "sunset", "sunrise", "dusk", "twilight",
        "night", "nighttime", "evening", "dark", "blue_hour"
    ],
    "mood_style": [
        "bright", "dark", "vibrant", "muted", "colorful", "monochrome",
        "warm", "cool", "sunny", "cloudy", "rainy", "foggy",
        "sharp", "blurry", "soft", "high_contrast", "low_contrast",
        "vintage", "modern", "minimalist", "busy", "empty",
        "calm", "energetic", "peaceful", "chaotic", "romantic"
    ],
    "lighting": [
        "natural_light", "artificial_light", "backlighting", "side_lighting",
        "harsh_light", "soft_light", "golden_light", "blue_light",
        "indoor_light", "outdoor_light", "shadow", "highlights"
    ],
    "weather": [
        "sunny", "cloudy", "overcast", "rainy", "snowy", "foggy",
        "clear_sky", "stormy", "windy", "misty"
    ],
    "color_dominant": [
        "blue", "green", "red", "yellow", "orange", "purple",
        "warm_tones", "cool_tones", "neutral", "saturated", "desaturated"
    ]
}

def _compress_image(image_path: Path, max_size_mb: float = 4.0) -> bytes:
    """Compress image to fit Claude's 5MB limit with safety margin."""
    img = Image.open(image_path)

    # Convert RGBA to RGB if necessary
    if img.mode in ("RGBA", "LA", "P"):
        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
        rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = rgb_img

    # Resize if very large
    if img.width > 2000 or img.height > 2000:
        img.thumbnail((2000, 2000), Image.Resampling.LANCZOS)

    max_size_bytes = int(max_size_mb * 1024 * 1024)
    quality = 85

    while True:
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        output_size = output.tell()

        if output_size <= max_size_bytes or quality <= 30:
            output.seek(0)
            return output.read()

        quality = max(30, quality - 5)


def tag_image_with_claude(image_path: Path, *, threshold: float = 0.55) -> dict[str, Any]:
    """
    Tag an image using Claude Vision.
    Returns comprehensive semantic metadata with confidence scores.
    """
    if not image_path.exists():
        return {"error": f"File not found: {image_path}"}

    try:
        compressed = _compress_image(image_path)
        image_data = base64.standard_b64encode(compressed).decode("utf-8")
    except Exception as e:
        return {"error": f"Failed to compress/encode image: {e}"}

    # Determine media type
    suffix = image_path.suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    media_type = media_type_map.get(suffix, "image/jpeg")

    # Build tagging prompt
    categories_str = "\n".join([
        f"{cat}: {', '.join(tags)}"
        for cat, tags in TAG_CATEGORIES.items()
    ])

    prompt = f"""Analyze this travel/lifestyle photo and tag it comprehensively.

For each category below, identify which tags apply (0.0-1.0 confidence):
{categories_str}

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "scene_type": [{{"tag": "...", "confidence": 0.85}}, ...],
  "objects": [{{"tag": "...", "confidence": 0.90}}, ...],
  "activity": [...],
  "location_type": [...],
  "time_of_day": [...],
  "mood_style": [...],
  "lighting": [...],
  "weather": [...],
  "color_dominant": [...],
  "description": "one sentence summary of what the photo shows"
}}

Rules:
1. Only include tags with confidence >= 0.5
2. Order by descending confidence within each category
3. Maximum 5 tags per category
4. Confidence values must be precise (e.g., 0.89, not 0.9)
"""

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        }
                    ],
                }
            ],
        )

        result_text = response.content[0].text
        # Remove markdown code blocks if present
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        result_text = result_text.strip()

        tags = json.loads(result_text)

        # Calculate overall confidence
        all_confidences = []
        for category, items in tags.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and "confidence" in item:
                        all_confidences.append(item["confidence"])

        overall_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        tags["overall_confidence"] = round(overall_confidence, 3)
        tags["tags_found"] = len(all_confidences)

        return tags

    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON response: {e}"}
    except Exception as e:
        return {"error": f"Claude API error: {e}"}


def tag_hdd_batch(db_path: Path, hdd_root: Path, *, limit: int = 50):
    """
    Tag HDD photos in batch using Claude Vision.
    Updates database with comprehensive semantic tags.
    """
    if not db_path.exists():
        print(f"✗ Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get pending HDD photos
    sql = """
    SELECT source_id, source_path, filename
    FROM asset_index
    WHERE source_type = 'external_hdd'
      AND (scene_ml IS NULL OR scene_ml = '')
      AND is_personal = 0
    ORDER BY quality_score DESC, selection_score DESC
    LIMIT ?
    """

    rows = conn.execute(sql, (limit,)).fetchall()
    print(f"[yo_semantic_tagger] Tagging {len(rows)} HDD photos with Claude Vision...")

    updated = 0
    errors = 0

    for i, row in enumerate(rows, 1):
        source_id = row["source_id"]
        source_path = Path(row["source_path"])
        filename = row["filename"]

        if not source_path.exists():
            print(f"  [{i}] ✗ {filename}: file not found")
            errors += 1
            continue

        print(f"  [{i}] tagging {filename}...", end=" ", flush=True)

        tags = tag_image_with_claude(source_path)

        if "error" in tags:
            print(f"✗ {tags['error']}")
            errors += 1
            continue

        # Update database
        try:
            conn.execute(
                """
                UPDATE asset_index
                SET
                    scene_ml = ?,
                    objects_json = ?,
                    time_of_day = ?,
                    location_specifics = ?
                WHERE source_id = ?
                """,
                (
                    json.dumps(tags.get("scene_type", []), ensure_ascii=False),
                    json.dumps(tags.get("objects", []), ensure_ascii=False),
                    json.dumps(tags.get("time_of_day", []), ensure_ascii=False),
                    json.dumps({
                        "location_type": tags.get("location_type", []),
                        "mood_style": tags.get("mood_style", []),
                        "lighting": tags.get("lighting", []),
                        "weather": tags.get("weather", []),
                        "color": tags.get("color_dominant", []),
                        "description": tags.get("description", ""),
                    }, ensure_ascii=False),
                    source_id,
                ),
            )
            updated += 1
            conn.commit()

            confidence = tags.get("overall_confidence", 0)
            tags_count = tags.get("tags_found", 0)
            status = "✓" if confidence >= 0.65 else "⚠"
            print(f"{status} conf={confidence:.2f}, {tags_count} tags")

        except Exception as e:
            print(f"✗ DB error: {e}")
            errors += 1

    conn.close()
    print(f"[yo_semantic_tagger] Updated {updated}/{len(rows)} photos ({errors} errors)")


if __name__ == "__main__":
    import sys

    DB_PATH = Path(__file__).parent / "data" / "visual_memory.db"
    HDD_ROOT = Path("/Volumes/LaCie Travel")

    # Accept limit as command line argument, default to 50
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50

    tag_hdd_batch(DB_PATH, HDD_ROOT, limit=limit)
