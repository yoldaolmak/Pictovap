# YO_OS_VIL — Two-Pass Semantic Tagging System
## Final Brief for Claude Sonnet 4.6 (with Mac Photos Integration)

---

## Project Goal

Process 226,923 travel photos (Canon 60D HDD archive) through two-pass semantic tagging:
- **Pass 1 (Quick):** Location, color, objects, weather, people count, Kemal Kaya identification
- **Pass 2 (Deep):** Claude Vision narrative understanding, landmarks, activities

Enable queries like:
- "Kelebekler Vadisi insanlar var mı?" → Butterfly Valley photos with people
- "Kemal Kaya teknede resimler" → Kemal Kaya on boat
- "Kekova 5 foto" → Top 5 Kekova photos

---

## Critical Discovery: Mac Photos Integration

### Mac Photos Face Database
```
ZPERSON table:
  Z_PK=17711: "Kemal Kaya" (ZVERIFIEDTYPE=1)
  ZFACECOUNT: 4038 verified detections

ZDETECTEDFACE table (related to Z_PK=17711):
  Count: 4760 face records
  Fields: ZCENTERX, ZCENTERY, ZSIZE, ZQUALITY, ZASSET, ZFACEPRINT
  Status: All VERIFIED (confirmed by user in Mac Photos)
```

### Strategy: Use Mac Photos Verified Faces for Training

Instead of collecting 10-20 reference photos:
1. **Extract 4760 verified Kemal Kaya faces from Mac Photos**
   - Query: `SELECT * FROM ZDETECTEDFACE WHERE ZPERSON=17711 AND ZHIDDEN=0`
   - Extract bounding boxes + quality scores
   - Link to ZASSET (photo ID)

2. **Compute face descriptors from verified faces**
   - Use dlib face_recognition library (128-D embeddings)
   - Average embeddings from all 4760 faces → canonical Kemal Kaya representation
   - Store mean + standard deviation for threshold matching

3. **Scan HDD 226K for matches**
   - Detect all faces (OpenCV Haar Cascades or dlib)
   - Compute descriptors for each face
   - Compare to Kemal Kaya canonical representation
   - Tag matches with confidence > 0.6

---

## System Architecture

### Phase 0: Preparation
```
Step 1: Extract Mac Photos Kemal Kaya faces (4760)
├─ Read ZDETECTEDFACE (Z_PK, ZCENTERX, ZCENTERY, ZSIZE, ZASSET)
├─ Get ZASSET → source path, filename
├─ Extract face regions using bounding boxes
└─ Compute dlib 128-D face descriptors

Step 2: Compute canonical Kemal Kaya representation
├─ Average 4760 descriptors → mean vector
├─ Compute std deviation for confidence threshold
└─ Store in memory for HDD scanning
```

### Phase 1: Quick Pass (ALL 226K photos)

**1A. Path-based location extraction**
```
Input: /Volumes/LaCie Travel/Turkiye/Ege/İzmir/Çeşme/Alaçatı/photo.jpg
Output: location_tags = ["alaçatı", "çeşme", "izmir", "ege", "turkiye"]

Implementation:
- Parse filesystem hierarchy
- Build path→tags mapping (lower-cased, Turkish chars normalized)
- Store in: asset_index.location_tags
```

**1B. Fast visual detection (OpenCV)**
```
For each of 226K photos:
  1. Read image
  2. Detect dominant color (OpenCV histogram)
  3. Detect faces (Haar Cascades, count)
  4. Detect weather (sky color, rain, fog heuristics)
  5. Detect panorama (aspect ratio > 1.5)
  
Store in:
  - color_dominant TEXT       ("blue", "green", "orange")
  - people_count INT         (0, 1, 2, 5...)
  - weather_conditions TEXT  (["sunny", "clear_sky"])
  - composition TEXT         (["panoramic"])

Performance: ~100-120 hours CPU (can run overnight)
```

**1C. Kemal Kaya face recognition**
```
For each of 226K photos:
  1. Detect all faces (dlib)
  2. Compute 128-D descriptors for each face
  3. Compare to canonical Kemal Kaya representation
  4. If distance < threshold (0.6):
       tag_as("Kemal Kaya", confidence=distance)
  
Store in:
  - kemal_kaya_confidence REAL (0-1, >0.85 = high confidence)

Performance: ~40-60 hours CPU (face detection is slower)
```

**Pass 1 Result:** All 226K photos with basic tags + Kemal Kaya identification

---

### Phase 2: Deep Pass (All or subset, async)

```
For each photo (or highest-quality subset):
  1. Send image to Claude Vision
  2. Request: Activity, landmarks, narrative, relationships
  3. Parse response
  4. Store in semantic_tags_json

Store in:
  - semantic_tags_json TEXT
  
Performance: ~200-300 hours (API-bound, ~5 photos/min)
Can run in background, async
```

---

### Phase 3: Deduplication (Optional)

```
For all 226K photos:
  1. Compute perceptual hash (phash)
  2. Group by Hamming distance ≤ 8 (LOOSE threshold)
  3. For each group: keep BEST + important variants
  4. Mark canonical photos
  
Result: ~180-200K canonical + variants kept
Philosophy: "Keep story variants, not just single 'best'"
```

---

## Database Schema

```sql
asset_index (226K rows)
├── location_tags TEXT              -- ["alaçatı", "çeşme", "izmir"]
├── color_dominant TEXT             -- "blue", "green", etc.
├── people_count INT                -- 0, 1, 2, 5...
├── weather_conditions TEXT         -- ["sunny", "clear_sky", "open_air"]
├── composition TEXT                -- ["panoramic", "landscape"]
├── kemal_kaya_confidence REAL      -- 0-1, match confidence
├── basic_tags_json TEXT            -- Pass 1 output (quick)
├── semantic_tags_json TEXT         -- Pass 2 output (deep)
├── perceptual_hash TEXT            -- For deduplication
└── canonical BOOLEAN               -- Keep this variant?
```

---

## Implementation Roadmap

### Step 1: Mac Photos Face Extraction (Prep Phase)
```python
# Extract 4760 Kemal Kaya faces from Mac Photos
import sqlite3
from pathlib import Path

photos_db = Path.home() / "Pictures/Photos Library.photoslibrary/database/Photos.sqlite"
conn = sqlite3.connect(photos_db)
conn.row_factory = sqlite3.Row

kemal_faces = conn.execute("""
    SELECT df.Z_PK, df.ZCENTERX, df.ZCENTERY, df.ZSIZE, 
           a.ZFILENAME, a.ZDIRECTORY
    FROM ZDETECTEDFACE df
    JOIN ZASSET a ON df.ZASSET = a.Z_PK
    WHERE df.ZPERSON = 17711 AND df.ZHIDDEN = 0
""").fetchall()

print(f"Extracted {len(kemal_faces)} Kemal Kaya faces from Mac Photos")

# For each face: extract region, compute descriptor
# Store descriptors for matching
```

### Step 2: Phase 1 Location Extraction
```python
# Parse filesystem → location tags
import os
from pathlib import Path

hdd_root = Path("/Volumes/LaCie Travel")
location_map = {}

for photo_path in hdd_root.rglob("*.jpg"):
    # Extract hierarchy: Turkiye/Ege/İzmir/Çeşme/Alaçatı
    parts = photo_path.parts
    try:
        start_idx = parts.index("LaCie Travel") + 1
        location_parts = parts[start_idx:-1]  # Exclude filename
        tags = [p.lower() for p in location_parts]  # Normalize
        location_map[str(photo_path)] = tags
    except ValueError:
        continue

print(f"Mapped {len(location_map)} photos to locations")
```

### Step 3: Phase 1 Color + Objects + Weather Detection
```python
# Fast visual detection for all 226K
import cv2
import numpy as np
from pathlib import Path

def analyze_photo_fast(image_path):
    img = cv2.imread(str(image_path))
    if img is None:
        return None
    
    # Dominant color
    pixels = img.reshape((-1, 3))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, _, centers = cv2.kmeans(pixels.astype(np.float32), 1, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    dominant_color = centers[0].astype(int)
    
    # Face count
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 1.3, 5)
    
    # Panorama (aspect ratio)
    h, w = img.shape[:2]
    is_panorama = w / h > 1.5
    
    return {
        "color": dominant_color,
        "people_count": len(faces),
        "panorama": is_panorama
    }
```

### Step 4: Kemal Kaya Face Recognition
```python
# Match HDD faces to Kemal Kaya canonical representation
import dlib
import numpy as np

# Load canonical Kemal Kaya descriptor (from Step 1)
kemal_canonical = np.load("kemal_kaya_canonical.npy")
kemal_std = np.load("kemal_kaya_std.npy")

face_detector = dlib.get_frontal_face_detector()
face_recognizer = dlib.face_recognition_model_v1("mmod_human_face_detector.dat")

def match_kemal_kaya(image_path, threshold=0.6):
    img = dlib.load_rgb_image(str(image_path))
    dets = face_detector(img, 1)
    
    matches = []
    for det in dets:
        shape = face_recognizer.compute_face_descriptor(img, det)
        descriptor = np.array(shape)
        
        distance = np.linalg.norm(descriptor - kemal_canonical)
        confidence = 1.0 - (distance / 2.0)  # Normalize to 0-1
        
        if confidence > threshold:
            matches.append({
                "confidence": confidence,
                "bbox": (det.left(), det.top(), det.right(), det.bottom())
            })
    
    return matches
```

### Step 5: Phase 2 Claude Vision (Async)
```python
# Narrative tagging via Claude Vision
import anthropic
import json

client = anthropic.Anthropic()

def tag_narrative(image_path, location_tags):
    # Compress and send to Claude
    prompt = f"""
    Photo location: {', '.join(location_tags)}
    
    Analyze this travel photo. Provide:
    - Activity (hiking, market, boat tour, meal, etc.)
    - Landmark (if identifiable)
    - Narrative (brief story about what this photo captures)
    - Relationships (does this connect to other photos?)
    
    Return JSON:
    {{
        "activity": "...",
        "landmark": "...",
        "narrative": "...",
        "relationships": [...]
    }}
    """
    
    # ... call Claude Vision API ...
    # Store result in semantic_tags_json
```

---

## Timeline & Resource Estimates

| Phase | Task | Duration | Notes |
|-------|------|----------|-------|
| **Prep** | Extract Mac Photos faces (4760) | 30 min | One-time |
| **Prep** | Compute descriptors + canonical | 1 hour | One-time |
| **Phase 1A** | Location extraction (226K) | 2-3 hours | Filesystem walk |
| **Phase 1B** | Color/objects/weather (226K) | 100-120 hours | CPU-bound, OpenCV |
| **Phase 1C** | Kemal Kaya matching (226K) | 40-60 hours | dlib face detection slower |
| **Phase 1 Total** | Quick pass all 226K | **142-183 hours** | Can run overnight, multiple nights |
| **Phase 2** | Deep pass (all or subset) | 200-300 hours | API async, non-blocking |
| **Phase 3** | Deduplication (optional) | 10-20 hours | phash + grouping |
| **TOTAL** | Complete system | **352-503 hours** | ~15-20 days continuous (or 4-6 weeks part-time) |

---

## Questions for Sonnet

1. **Face Recognition Library:** Use dlib (best accuracy, slower) or face_recognition (OpenCV wrapper, faster)?

2. **Mac Photos Descriptor Extraction:**
   - Extract faces from Mac Photos directly (use bounding boxes)?
   - Or match ZASSET photos in HDD, then extract?

3. **Kemal Kaya Confidence Threshold:**
   - Start at 0.6, adjust based on false positives?
   - Should we have high-confidence (>0.85) and medium-confidence (0.6-0.85) tags?

4. **Phase 1 vs Phase 2 Parallelization:**
   - Run all Phase 1 on Mac (CPU-bound)?
   - Move Phase 2 to server if available (API-bound)?
   - Or interleave?

5. **Deduplication Timing:**
   - After Phase 1 (tag 180-200K, skip duplicates)?
   - Or after Phase 2 (full semantic tags on all 226K)?

6. **Storage Strategy:**
   - Store all data in visual_memory.db?
   - Or export to JSON per photo for WordPress?

---

## Success Criteria

✅ Extract 4760 Kemal Kaya verified faces from Mac Photos  
✅ Compute canonical Kemal Kaya face descriptor  
✅ All 226K photos indexed with location tags  
✅ All 226K photos analyzed for color/objects/weather/panorama  
✅ All 226K photos scanned for Kemal Kaya (high + medium confidence)  
✅ All/most tagged with semantic metadata (narrative, landmarks, activity)  
✅ "Kemal Kaya teknede" → Kemal on boat photos  
✅ "Kelebekler Vadisi insanlar" → Butterfly Valley with people  
✅ Ready for WordPress upload with full metadata  

---

## Why This Approach Works

✅ **4760 verified training faces** = professional-grade training data  
✅ **Two-pass system** = quick basic tags immediately, deep tags async  
✅ **Location-aware** = filesystem structure leveraged automatically  
✅ **$0 budget** = free libraries only (dlib, OpenCV, Claude API separate)  
✅ **Scalable** = Phase 1 can run on any CPU, Phase 2 async  
✅ **Story-focused** = tags tell narrative, not just inventory  
✅ **Mac Photos integration** = leverage existing verified data  

---

**Ready to code. Awaiting Sonnet's architectural decisions.**
