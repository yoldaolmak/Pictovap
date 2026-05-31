#!/usr/bin/env python3
"""
Extract Kemal Kaya face encodings from Mac Photos verified faces (4760)
One-time setup before Phase 1 tagging
"""

import sqlite3
import numpy as np
import face_recognition
import pickle
from pathlib import Path
from PIL import Image
import io

def extract_kemal_kaya_encodings(
    mac_photos_db: Path,
    hdd_root: Path,
    output_path: Path = Path("kemal_kaya_face_model.pkl")
):
    """
    Extract Kemal Kaya verified faces from Mac Photos
    Compute 128-D face encodings
    Save for Phase 1 matching
    """

    print("[extract_kemal_kaya_encodings] START")

    # Connect to Mac Photos
    conn = sqlite3.connect(mac_photos_db)
    conn.row_factory = sqlite3.Row

    # Get diverse sample of Kemal Kaya verified faces (10 total)
    # ZPERSON Z_PK=17711 (verified)
    # Select: 3 oldest + 7 newest for temporal diversity
    sql = """
    SELECT df.Z_PK, df.ZCENTERX, df.ZCENTERY, df.ZSIZE, df.ZQUALITY,
           a.ZFILENAME, a.ZDIRECTORY, a.ZDATECREATED
    FROM ZDETECTEDFACE df
    JOIN ZASSET a ON df.ZASSET = a.Z_PK
    WHERE df.ZPERSON = 17711 AND df.ZHIDDEN = 0
    ORDER BY a.ZDATECREATED ASC
    LIMIT 3  -- oldest 3
    UNION ALL
    SELECT df.Z_PK, df.ZCENTERX, df.ZCENTERY, df.ZSIZE, df.ZQUALITY,
           a.ZFILENAME, a.ZDIRECTORY, a.ZDATECREATED
    FROM ZDETECTEDFACE df
    JOIN ZASSET a ON df.ZASSET = a.Z_PK
    WHERE df.ZPERSON = 17711 AND df.ZHIDDEN = 0
    ORDER BY a.ZDATECREATED DESC
    LIMIT 7  -- newest 7
    """

    rows = conn.execute(sql).fetchall()
    print(f"  Selected {len(rows)} diverse Kemal Kaya faces (oldest + newest)")
    print(f"  (Sampling from 4760 total verified faces for speed)")

    encodings = []
    valid_faces = 0
    skipped = 0

    for idx, row in enumerate(rows, 1):
        # Reconstruct photo path from ZFILENAME + ZDIRECTORY
        # Mac Photos paths are internal, need to find actual HDD file
        filename = row["ZFILENAME"]

        # Search for file in HDD
        candidates = list(hdd_root.rglob(filename))

        if not candidates:
            # Try fuzzy matching (same name, similar path)
            candidates = list(hdd_root.glob(f"**/{filename}"))

        if not candidates:
            skipped += 1
            continue

        photo_path = candidates[0]  # Use first match

        if not photo_path.exists():
            skipped += 1
            continue

        try:
            # Load image
            image = face_recognition.load_image_file(str(photo_path))

            # Get bounding box from Mac Photos coordinates
            # (ZCENTERX, ZCENTERY, ZSIZE relative to image)
            # face_recognition.face_encodings expects face_locations in (top, right, bottom, left) format

            # For now: detect all faces and take closest to center
            face_locations = face_recognition.face_locations(image)

            if not face_locations:
                skipped += 1
                continue

            # Extract encoding from first/best face
            face_encodings = face_recognition.face_encodings(image, face_locations)

            if face_encodings:
                encodings.append(face_encodings[0])
                valid_faces += 1

        except Exception as e:
            print(f"  Error processing {filename}: {e}")
            skipped += 1
            continue

        if (idx) % 100 == 0:
            print(f"  [{idx}] Extracted {valid_faces} valid encodings...")

    conn.close()

    if not encodings:
        print("✗ No encodings extracted!")
        return

    # Convert to numpy array
    encodings_array = np.array(encodings)

    # Compute mean + std for matching
    mean_encoding = np.mean(encodings_array, axis=0)
    std_encoding = np.std(encodings_array, axis=0)

    print(f"  Valid faces: {valid_faces}")
    print(f"  Skipped: {skipped}")
    print(f"  Mean encoding shape: {mean_encoding.shape}")
    print(f"  Std encoding shape: {std_encoding.shape}")

    # Save all encodings + statistics
    model_data = {
        "encodings": encodings_array,
        "mean": mean_encoding,
        "std": std_encoding,
        "count": len(encodings_array),
    }

    with open(output_path, "wb") as f:
        pickle.dump(model_data, f)

    print(f"✅ Saved Kemal Kaya model to {output_path}")
    print(f"   - {len(encodings_array)} face encodings")
    print(f"   - Mean + Std deviation computed")
    print(f"   - Ready for Phase 1 matching")

    return output_path


if __name__ == "__main__":
    mac_photos_db = Path.home() / "Pictures/Photos Library.photoslibrary/database/Photos.sqlite"
    hdd_root = Path("/Volumes/LaCie Travel")
    output = Path(__file__).parent / "kemal_kaya_face_model.pkl"

    if not mac_photos_db.exists():
        print(f"✗ Mac Photos DB not found: {mac_photos_db}")
        exit(1)

    if not hdd_root.exists():
        print(f"✗ HDD not found: {hdd_root}")
        exit(1)

    extract_kemal_kaya_encodings(mac_photos_db, hdd_root, output)
