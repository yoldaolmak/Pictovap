#!/usr/bin/env python3
"""
Extract Kemal Kaya face encodings from Mac Photos verified faces
Uses dlib directly if face_recognition library has import issues
Optimized: 10 diverse faces (3 oldest + 7 newest) instead of all 4760
"""

import sqlite3
import numpy as np
import pickle
from pathlib import Path
from PIL import Image
import cv2
import dlib
import io

def extract_kemal_kaya_encodings_dlib(
    mac_photos_db: Path,
    hdd_root: Path,
    output_path: Path = Path("kemal_kaya_face_model.pkl")
):
    """
    Extract Kemal Kaya verified faces from Mac Photos
    Compute 128-D face encodings using dlib
    Save for Phase 1 matching
    """

    print("[extract_kemal_kaya_encodings] START")

    # Initialize dlib face recognizer
    try:
        face_recognizer = dlib.face_recognition_model_v1(
            "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/face_recognition_models/models/dlib_face_recognition_resnet_model_v1.dat"
        )
        detector = dlib.get_frontal_face_detector()
        print("  Using dlib directly for face encoding")
    except Exception as e:
        print(f"  ✗ Could not load dlib models: {e}")
        return None

    # Connect to Mac Photos
    conn = sqlite3.connect(mac_photos_db)
    conn.row_factory = sqlite3.Row

    # Get diverse sample of Kemal Kaya verified faces (10 total)
    # ZPERSON Z_PK=17711 (verified)
    # Select: 3 oldest + 7 newest for temporal diversity
    sql = """
    SELECT * FROM (
        SELECT df.Z_PK, df.ZCENTERX, df.ZCENTERY, df.ZSIZE, df.ZQUALITY,
               a.ZFILENAME, a.ZDIRECTORY, a.ZDATECREATED
        FROM ZDETECTEDFACE df
        JOIN ZASSET a ON df.ZASSET = a.Z_PK
        WHERE df.ZPERSON = 17711 AND df.ZHIDDEN = 0
        ORDER BY a.ZDATECREATED ASC
        LIMIT 3
    )
    UNION ALL
    SELECT * FROM (
        SELECT df.Z_PK, df.ZCENTERX, df.ZCENTERY, df.ZSIZE, df.ZQUALITY,
               a.ZFILENAME, a.ZDIRECTORY, a.ZDATECREATED
        FROM ZDETECTEDFACE df
        JOIN ZASSET a ON df.ZASSET = a.Z_PK
        WHERE df.ZPERSON = 17711 AND df.ZHIDDEN = 0
        ORDER BY a.ZDATECREATED DESC
        LIMIT 7
    )
    """

    rows = conn.execute(sql).fetchall()
    print(f"  Selected {len(rows)} diverse Kemal Kaya faces (oldest + newest)")
    print(f"  (Sampling from 4760 total verified faces for speed)")

    encodings = []
    valid_faces = 0
    skipped = 0

    for idx, row in enumerate(rows, 1):
        filename = row["ZFILENAME"]

        # Search for file in HDD
        candidates = list(hdd_root.rglob(filename))

        if not candidates:
            candidates = list(hdd_root.glob(f"**/{filename}"))

        if not candidates:
            print(f"  [{idx}] ✗ File not found: {filename}")
            skipped += 1
            continue

        photo_path = candidates[0]

        if not photo_path.exists():
            skipped += 1
            continue

        try:
            # Load image with dlib
            img_array = np.array(dlib.load_rgb_image(str(photo_path)))

            # Detect faces
            dets = detector(img_array, 1)

            if not dets:
                skipped += 1
                continue

            # Get encoding from first/best face
            for det in dets:
                try:
                    face_encoding = face_recognizer.compute_face_descriptor(img_array, det)
                    encodings.append(np.array(face_encoding))
                    valid_faces += 1
                    break  # Only use first face per image
                except Exception as e:
                    skipped += 1
                    continue

        except Exception as e:
            print(f"  Error processing {filename}: {e}")
            skipped += 1
            continue

        if (idx) % 3 == 0:
            print(f"  [{idx}/{len(rows)}] Extracted {valid_faces} valid encodings...")

    conn.close()

    if not encodings:
        print("✗ No encodings extracted!")
        return None

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

    extract_kemal_kaya_encodings_dlib(mac_photos_db, hdd_root, output)
