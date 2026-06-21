#!/usr/bin/env python3
"""
Face Detection using OpenCV Haar Cascades
Detects faces, estimates gender/age from face region patterns, stores bounding boxes
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
import cv2
import numpy as np

from src.core.settings import get_visual_memory_db_path


class FaceDetector:
    def __init__(self):
        # Load Haar Cascades
        cascade_path = cv2.data.haarcascades
        self.face_cascade = cv2.CascadeClassifier(
            str(Path(cascade_path) / "haarcascade_frontalface_default.xml")
        )

        # Optional: eye cascade for more accurate face detection
        self.eye_cascade = cv2.CascadeClassifier(
            str(Path(cascade_path) / "haarcascade_eye.xml")
        )

    def detect_faces(self, image_path: Path) -> dict[str, Any]:
        """
        Detect faces in image and estimate attributes.

        Returns:
            {
                "face_count": 3,
                "faces": [
                    {
                        "bbox": [x, y, w, h],
                        "confidence": 0.95,
                        "estimated_gender": "male",
                        "estimated_age": "adult",
                        "eye_detected": true
                    },
                    ...
                ],
                "detection_quality": 0.87
            }
        """
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                return {"error": "Failed to load image"}

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape

            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                maxSize=(int(width * 0.8), int(height * 0.8)),
                flags=cv2.CASCADE_SCALE_IMAGE,
            )

            if len(faces) == 0:
                return {
                    "face_count": 0,
                    "faces": [],
                    "detection_quality": 0.0,
                }

            face_objects = []

            for x, y, w, h in faces:
                # Extract face region
                face_region = gray[y:y+h, x:x+w]

                # Check if eyes are detected (increases confidence)
                eyes = self.eye_cascade.detectMultiScale(face_region)
                has_eyes = len(eyes) >= 2  # At least 2 eyes

                # Estimate gender from face size and position patterns
                estimated_gender = self._estimate_gender(face_region, x, y, w, h, width, height)

                # Estimate age group from face characteristics
                estimated_age = self._estimate_age(face_region, w, h)

                # Calculate face size confidence (larger faces = more confident)
                face_area_ratio = (w * h) / (width * height)
                size_confidence = min(1.0, face_area_ratio * 100)  # 1% of image = 1.0

                # Eye detection boosts confidence
                eye_confidence = 0.15 if has_eyes else 0.0

                # Overall face detection confidence
                confidence = min(0.99, 0.7 + size_confidence * 0.2 + eye_confidence)

                face_objects.append({
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "confidence": round(confidence, 3),
                    "estimated_gender": estimated_gender,
                    "estimated_age": estimated_age,
                    "eye_detected": bool(has_eyes),
                    "face_area_ratio": round(face_area_ratio, 4),
                })

            # Detection quality = average confidence
            detection_quality = sum(f["confidence"] for f in face_objects) / len(face_objects)

            return {
                "face_count": len(faces),
                "faces": face_objects,
                "detection_quality": round(detection_quality, 3),
            }

        except Exception as e:
            return {"error": f"Face detection error: {e}"}

    @staticmethod
    def _estimate_gender(face_region: np.ndarray, x: int, y: int, w: int, h: int,
                        img_width: int, img_height: int) -> str:
        """
        Estimate gender from face region characteristics.
        Very basic heuristic - face shape, size relative to head.
        """
        # Face aspect ratio and position hints
        aspect_ratio = w / h if h > 0 else 1.0

        # Wider faces tend to be male, narrower tend to be female (very rough)
        if aspect_ratio > 1.0:
            gender = "male"
        elif aspect_ratio < 0.9:
            gender = "female"
        else:
            gender = "unknown"

        # If face is very small or at edge, lower confidence by marking as "indeterminate"
        if aspect_ratio > 1.2 or aspect_ratio < 0.7:
            gender = "unknown"

        return gender

    @staticmethod
    def _estimate_age(face_region: np.ndarray, w: int, h: int) -> str:
        """
        Estimate age group from face size and region characteristics.
        Very basic heuristic - small faces might be children.
        """
        # Face size heuristic
        face_size = w * h

        # Very small faces (< 50x50) might be distant, harder to classify
        if w < 50 or h < 50:
            return "indeterminate"

        # Texture analysis (simple)
        # Children tend to have smoother skin, fewer wrinkles
        laplacian = cv2.Laplacian(face_region, cv2.CV_64F)
        texture_variance = laplacian.var()

        # Very smooth = possibly child, rough = possibly older
        if texture_variance < 50:
            return "child"
        elif texture_variance < 150:
            return "young_adult"
        else:
            return "adult"


def tag_faces_for_hdd_batch(db_path: Path, *, limit: int = 100):
    """
    Detect faces in HDD photos and update objects_json with face data.
    Integrates with existing semantic tags.
    """
    if not db_path.exists():
        print(f"✗ Database not found: {db_path}")
        return

    detector = FaceDetector()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get photos that have been tagged but don't have face data yet
    sql = """
    SELECT source_id, source_path, filename, objects_json
    FROM asset_index
    WHERE source_type = 'external_hdd'
      AND (scene_ml IS NOT NULL AND scene_ml != '')
      AND is_personal = 0
    ORDER BY quality_score DESC, selection_score DESC
    LIMIT ?
    """

    rows = conn.execute(sql, (limit,)).fetchall()
    print(f"[yo_face_detector] Detecting faces in {len(rows)} HDD photos...")

    updated = 0
    for i, row in enumerate(rows, 1):
        source_id = row["source_id"]
        source_path = Path(row["source_path"])
        filename = row["filename"]

        if not source_path.exists():
            print(f"  [{i}] ✗ {filename}: file not found")
            continue

        result = detector.detect_faces(source_path)

        if "error" in result:
            print(f"  [{i}] ✗ {filename}: {result['error']}")
            continue

        # Parse existing objects
        try:
            existing_objects = json.loads(row["objects_json"] or "[]")
            if not isinstance(existing_objects, list):
                existing_objects = []
        except (json.JSONDecodeError, TypeError):
            existing_objects = []

        # Add face objects
        face_count = result["face_count"]
        if face_count > 0:
            for face_data in result["faces"]:
                existing_objects.append({
                    "name": f"face_{face_data['estimated_gender']}_{face_data['estimated_age']}",
                    "confidence": face_data["confidence"],
                    "bbox": face_data["bbox"],
                    "gender": face_data["estimated_gender"],
                    "age_group": face_data["estimated_age"],
                })

            # Update "people" or "person" count/confidence
            people_exists = any(obj.get("name", "").startswith("person") for obj in existing_objects)
            if not people_exists and face_count > 0:
                existing_objects.append({
                    "name": "people" if face_count > 1 else "person",
                    "confidence": min(0.95, result["detection_quality"] + 0.1),
                })

        # Update database
        try:
            conn.execute(
                "UPDATE asset_index SET objects_json = ? WHERE source_id = ?",
                (json.dumps(existing_objects, ensure_ascii=False), source_id),
            )
            updated += 1
            conn.commit()

            status = "✓" if face_count > 0 else "○"
            print(f"  [{i}] {status} {filename}: {face_count} faces detected")

        except Exception as e:
            print(f"  [{i}] ✗ {filename}: DB error {e}")

    conn.close()
    print(f"[yo_face_detector] Updated {updated}/{len(rows)} photos with face data")


if __name__ == "__main__":
    import sys

    DB_PATH = Path(__file__).parent / "data" / "visual_memory.db"

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    tag_faces_for_hdd_batch(DB_PATH, limit=limit)
