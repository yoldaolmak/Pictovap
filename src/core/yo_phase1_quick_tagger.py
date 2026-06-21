#!/usr/bin/env python3
"""
YO_OS_VIL Phase 1: Quick Pass Tagger
Process ALL 226K photos with fast, local-only methods
Integrates with visual_memory.db
"""

import cv2
import numpy as np
import face_recognition
import pickle
import json
import imagehash
from pathlib import Path
import sqlite3
from PIL import Image
from datetime import datetime

class QuickPassTagger:
    def __init__(self, visual_memory_db: Path, kemal_model_path: Path):
        """
        Initialize tagger with visual_memory database and Kemal Kaya model

        Args:
            visual_memory_db: Path to visual_memory.db
            kemal_model_path: Path to kemal_kaya_face_model.pkl
        """
        self.db_path = visual_memory_db
        self.db = sqlite3.connect(visual_memory_db)
        self.cursor = self.db.cursor()

        # Load Kemal Kaya face model
        with open(kemal_model_path, "rb") as f:
            self.kemal_model = pickle.load(f)

        self.kemal_encodings = self.kemal_model["encodings"]
        self.kemal_mean = self.kemal_model["mean"]
        self.kemal_std = self.kemal_model["std"]

        print(f"  Loaded Kemal Kaya model: {len(self.kemal_encodings)} reference faces")

        # Ensure schema has quick-pass columns
        self._ensure_columns()

    def _ensure_columns(self):
        """Ensure visual_memory.db has all required columns for quick pass"""
        existing_columns = {
            row[1] for row in self.cursor.execute(
                "PRAGMA table_info(asset_index)"
            ).fetchall()
        }

        new_columns = {
            "location_tags": "TEXT",
            "color_dominant": "TEXT",
            "objects_detected": "TEXT",
            "people_count": "INTEGER",
            "kemal_kaya_confidence": "REAL",
            "weather_conditions": "TEXT",
            "composition": "TEXT",
            "basic_tags_json": "TEXT",
            "perceptual_hash": "TEXT",
            "quick_pass_done": "BOOLEAN DEFAULT 0",
        }

        with self.db:
            for col_name, col_type in new_columns.items():
                if col_name not in existing_columns:
                    self.cursor.execute(
                        f"ALTER TABLE asset_index ADD COLUMN {col_name} {col_type}"
                    )

    def process_photo(self, filepath: Path) -> dict | None:
        """Extract all basic tags from one photo"""

        try:
            filepath = Path(filepath)

            # 1. Location from path
            location_tags = self._extract_location_from_path(filepath)

            # 2. Load image
            img = cv2.imread(str(filepath))
            if img is None:
                return None

            # 3. Dominant color
            dominant_color = self._detect_dominant_color(img)

            # 4. Objects (placeholder for now)
            objects = []  # TODO: Haar cascades

            # 5. Face detection + Kemal recognition
            people_count, kemal_confidence = self._detect_faces_and_kemal(filepath)

            # 6. Weather/conditions
            weather = self._detect_weather_conditions(img)

            # 7. Composition
            composition = self._detect_composition(img)

            # 8. Perceptual hash
            pil_img = Image.open(filepath)
            phash = str(imagehash.phash(pil_img))

            # Combine to JSON
            basic_tags = {
                "location": location_tags,
                "color_dominant": dominant_color,
                "objects": objects,
                "people_count": people_count,
                "kemal_kaya": kemal_confidence,
                "weather": weather,
                "composition": composition,
            }

            # Update database using filename match
            filename = filepath.name
            self.cursor.execute(
                """
                UPDATE asset_index
                SET
                    location_tags = ?,
                    color_dominant = ?,
                    objects_detected = ?,
                    people_count = ?,
                    kemal_kaya_confidence = ?,
                    weather_conditions = ?,
                    composition = ?,
                    basic_tags_json = ?,
                    perceptual_hash = ?,
                    quick_pass_done = 1
                WHERE LOWER(filename) = LOWER(?)
                """,
                (
                    json.dumps(location_tags, ensure_ascii=False),
                    dominant_color,
                    json.dumps(objects, ensure_ascii=False),
                    people_count,
                    kemal_confidence,
                    json.dumps(weather, ensure_ascii=False),
                    composition,
                    json.dumps(basic_tags, ensure_ascii=False),
                    phash,
                    filename,
                ),
            )

            return basic_tags

        except Exception as e:
            print(f"  ✗ Error processing {filepath}: {e}")
            return None

    def _extract_location_from_path(self, filepath: Path) -> list[str]:
        """
        Extract location tags from filesystem path
        /Volumes/LaCie Travel/Turkiye/Ege/İzmir/Çeşme/Alaçatı/photo.jpg
        → ["alaçatı", "çeşme", "izmir", "ege", "turkiye"]
        """
        parts = filepath.parts

        # Find country-level folder
        country_idx = None
        for i, part in enumerate(parts):
            if part in ["Turkiye", "Yunanistan", "İtalya", "İspanya", "Portekiz"]:
                country_idx = i
                break

        if country_idx is None:
            return []

        # Extract location hierarchy (exclude filename, reverse order)
        location_parts = parts[country_idx:-1]
        return [p.lower() for p in reversed(location_parts)]

    def _detect_dominant_color(self, img: np.ndarray) -> str:
        """
        Detect dominant color using histogram
        Returns color name in Turkish
        """
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Get hue histogram
        hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        dominant_hue = np.argmax(hist)

        # Map hue to color
        if 100 <= dominant_hue <= 120:
            return "mavi"  # blue
        elif 35 <= dominant_hue < 77:
            return "yeşil"  # green
        elif 0 <= dominant_hue < 10 or 170 <= dominant_hue <= 180:
            return "kırmızı"  # red
        elif 10 <= dominant_hue < 25:
            return "turuncu"  # orange
        elif 25 <= dominant_hue < 35:
            return "sarı"  # yellow
        else:
            return "karışık"  # mixed

    def _detect_faces_and_kemal(self, filepath: Path) -> tuple[int, float | None]:
        """
        Detect all faces + identify Kemal Kaya
        Returns: (people_count, kemal_confidence)
        """
        try:
            # Load image for face_recognition
            image = face_recognition.load_image_file(str(filepath))

            # Detect all faces
            face_locations = face_recognition.face_locations(image, model="hog")
            people_count = len(face_locations)

            if people_count == 0:
                return 0, None

            # Get face encodings
            face_encodings_list = face_recognition.face_encodings(image, face_locations)

            # Compare with Kemal's encodings
            kemal_confidence = None
            for face_encoding in face_encodings_list:
                # Compare with Kemal reference encodings
                distances = face_recognition.face_distance(
                    self.kemal_encodings, face_encoding
                )

                min_distance = np.min(distances)
                confidence = 1.0 - min_distance  # 0-1 scale

                # High confidence threshold
                if confidence > 0.85:
                    kemal_confidence = round(confidence, 3)
                    break

                # Also try distance to mean
                dist_to_mean = np.linalg.norm(face_encoding - self.kemal_mean)
                mean_confidence = 1.0 - (dist_to_mean / 2.0)

                if mean_confidence > 0.85:
                    kemal_confidence = round(mean_confidence, 3)
                    break

            return people_count, kemal_confidence

        except Exception as e:
            print(f"    Face detection error: {e}")
            return 0, None

    def _detect_weather_conditions(self, img: np.ndarray) -> list[str]:
        """Detect weather/sky conditions"""
        # Check top 1/3 of image (sky region)
        h, w = img.shape[:2]
        sky_region = img[: h // 3, :]

        # Calculate brightness
        gray_sky = cv2.cvtColor(sky_region, cv2.COLOR_BGR2GRAY)
        brightness = gray_sky.mean()

        conditions = []

        if brightness > 180:
            conditions.append("açık gökyüzü")  # clear sky
        elif brightness > 120:
            conditions.append("bulutlu")  # cloudy
        else:
            conditions.append("kapalı")  # overcast

        # Check for blue sky
        hsv_sky = cv2.cvtColor(sky_region, cv2.COLOR_BGR2HSV)
        blue_mask = cv2.inRange(hsv_sky, (100, 50, 50), (120, 255, 255))
        if blue_mask.sum() > sky_region.size * 0.1:  # >10% blue
            conditions.append("mavi gökyüzü")

        return conditions

    def _detect_composition(self, img: np.ndarray) -> str:
        """Detect composition type"""
        h, w = img.shape[:2]
        aspect_ratio = w / h

        if aspect_ratio > 2.0:
            return "panoramik"
        elif aspect_ratio > 1.3:
            return "landscape"
        elif aspect_ratio < 0.8:
            return "portrait"
        else:
            return "square"

    def process_all(self, hdd_path: Path, limit: int | None = None):
        """Process all photos (or up to limit)"""
        hdd_path = Path(hdd_path)

        # Get all photos from HDD
        photos = list(hdd_path.rglob("*.JPG")) + list(hdd_path.rglob("*.jpg"))

        if limit:
            photos = photos[:limit]

        print(f"[yo_phase1_quick_tagger] Found {len(photos)} photos to process")

        processed = 0
        skipped = 0

        for idx, photo in enumerate(photos, 1):
            result = self.process_photo(photo)

            if result:
                processed += 1
            else:
                skipped += 1

            if idx % 50 == 0:
                self.db.commit()
                pct = (idx / len(photos)) * 100
                print(f"  [{idx}] {pct:.1f}% - {processed} processed, {skipped} skipped")

        self.db.commit()
        print(f"\n✅ Phase 1 Quick Pass Complete")
        print(f"   Processed: {processed}/{len(photos)}")
        print(f"   Skipped: {skipped}")
        print(f"   All photos tagged with basic metadata")

        self.db.close()


if __name__ == "__main__":
    db_path = Path(__file__).parent / "data" / "visual_memory.db"
    model_path = Path(__file__).parent / "kemal_kaya_face_model.pkl"

    if not db_path.exists():
        print(f"✗ Database not found: {db_path}")
        exit(1)

    if not model_path.exists():
        print(f"✗ Kemal model not found: {model_path}")
        print("  Run: python3 extract_kemal_kaya_faces.py")
        exit(1)

    hdd_path = Path("/Volumes/LaCie Travel")
    if not hdd_path.exists():
        print(f"✗ HDD not found: {hdd_path}")
        exit(1)

    tagger = QuickPassTagger(db_path, model_path)
    tagger.process_all(hdd_path)  # Can pass limit=1000 for testing
