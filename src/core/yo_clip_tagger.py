#!/usr/bin/env python3
"""
Semantic Tagger for HDD/Mac Photos using Claude Vision
Comprehensive tag taxonomy (Depositphotos-style) with confidence scores
"""
from __future__ import annotations

import json
import base64
import sqlite3
from pathlib import Path
from typing import Any
import anthropic

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
    "composition": [
        "portrait_orientation", "landscape_orientation", "square",
        "rule_of_thirds", "centered", "leading_lines", "symmetrical",
        "layered", "depth_of_field", "wide_angle", "zoom", "macro"
    ],
    "lighting": [
        "natural_light", "artificial_light", "backlighting", "side_lighting",
        "harsh_light", "soft_light", "golden_light", "blue_light",
        "indoor_light", "outdoor_light", "shadow", "highlights"
    ],
    "weather": [
        "sunny", "cloudy", "overcast", "rainy", "snowy", "foggy",
        "clear_sky", "stormy", "windy", "misty", "clear_weather"
    ],
    "color": [
        "blue_dominant", "green_dominant", "red_dominant", "yellow_dominant",
        "warm_colors", "cool_colors", "earthy_tones", "pastels",
        "saturated", "desaturated", "high_saturation", "low_saturation"
    ]
}

class CLIPSemanticTagger:
    def __init__(self, device: str = "auto"):
        self.device = self._get_device(device)
        print(f"  Loading CLIP model on {self.device}...")

        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        self.model.to(self.device)
        self.model.eval()
        torch.set_grad_enabled(False)

    @staticmethod
    def _get_device(device: str) -> str:
        if device == "auto":
            if torch.backends.mps.is_available():
                return "mps"
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    def tag_image(self, image_path: Path, *, top_k: int = 3, threshold: float = 0.15) -> dict[str, Any]:
        """
        Tag an image with all categories. Return top tags per category with confidence.

        Args:
            image_path: Path to image file
            top_k: Return top K tags per category
            threshold: Minimum confidence (0-1) to include a tag

        Returns:
            {
                "scene_type": [{"tag": "landscape", "confidence": 0.89}],
                "objects": [{"tag": "mountain", "confidence": 0.82}, ...],
                "activity": [...],
                ...
                "overall_confidence": 0.76
            }
        """
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            return {"error": f"Failed to load image: {e}"}

        results = {}
        confidences = []

        with torch.no_grad():
            for category, tags in TAG_CATEGORIES.items():
                # Prepare prompts for this category
                prompts = [f"a photo of {tag}" if category != "mood_style"
                          else f"this image has a {tag} mood"
                          for tag in tags]

                # Get embeddings
                inputs = self.processor(
                    text=prompts,
                    images=image,
                    return_tensors="pt",
                    padding=True
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                outputs = self.model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)[0].cpu().numpy()

                # Get top K tags
                top_indices = probs.argsort()[-top_k:][::-1]
                category_tags = []
                for idx in top_indices:
                    confidence = float(probs[idx])
                    if confidence >= threshold:
                        category_tags.append({
                            "tag": tags[idx],
                            "confidence": round(confidence, 3)
                        })
                        confidences.append(confidence)

                if category_tags:
                    results[category] = category_tags

        # Calculate overall confidence
        overall_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

        results["overall_confidence"] = overall_confidence
        results["tags_found"] = len(confidences)

        return results

def tag_hdd_batch(db_path: Path, hdd_root: Path, *, limit: int = 100, resume_from: str | None = None):
    """
    Tag HDD photos in batch using CLIP.
    Updates database with comprehensive semantic tags.
    """
    import sqlite3
    from datetime import datetime

    if not db_path.exists():
        print(f"✗ Database not found: {db_path}")
        return

    tagger = CLIPSemanticTagger()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get pending HDD photos
    sql = """
    SELECT source_id, source_path
    FROM asset_index
    WHERE source_type = 'external_hdd'
      AND (scene_ml IS NULL OR scene_ml = '')
      AND is_personal = 0
    ORDER BY quality_score DESC, created_at DESC
    LIMIT ?
    """

    rows = conn.execute(sql, (limit,)).fetchall()
    print(f"[yo_clip_tagger] Tagging {len(rows)} HDD photos...")

    updated = 0
    for i, row in enumerate(rows, 1):
        source_id = row["source_id"]
        source_path = Path(row["source_path"])

        if not source_path.exists():
            print(f"  [{i}] ✗ {source_id}: file not found")
            continue

        tags = tagger.tag_image(source_path)
        if "error" in tags:
            print(f"  [{i}] ✗ {source_id}: {tags['error']}")
            continue

        # Update database
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
                    "color": tags.get("color", []),
                }, ensure_ascii=False),
                source_id,
            ),
        )
        updated += 1

        # Progress
        confidence = tags.get("overall_confidence", 0)
        tags_count = tags.get("tags_found", 0)
        status = "✓" if confidence >= 0.6 else "⚠"
        print(f"  [{i}] {status} {source_path.name}: {tags_count} tags, conf={confidence:.2f}")

        if i % 10 == 0:
            conn.commit()
            print(f"    → Committed {i} photos")

    conn.commit()
    print(f"[yo_clip_tagger] Updated {updated}/{len(rows)} photos")
    conn.close()

if __name__ == "__main__":
    from pathlib import Path

    DB_PATH = Path(__file__).parent / "data" / "visual_memory.db"
    HDD_ROOT = Path("/Volumes/LaCie Travel")

    tag_hdd_batch(DB_PATH, HDD_ROOT, limit=20)
