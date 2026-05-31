# YO_OS_VIL Semantic Tagging System — Final Architectural Brief for Sonnet

## Critical Updates (User Clarifications - Apr 20, 2026)

### Mac Photos Library Status
- **Total:** 47,433 photos
- **HDD Import:** **0 (zero)** - LaCie Travel HDD photos are NOT imported to Mac Photos
- **Implication:** Cannot use Apple ML (ZMEDIAANALYSISASSETATTRIBUTES) for HDD photos
- **Solution:** Use Claude Vision for semantic tagging + local face recognition

### Tagging Philosophy (NOT Depositphotos-style)
NOT complex hierarchical taxonomy. Instead: **contextual, location-aware, narrative tags**.

**Example 1: Kelebekler Vadisi, Fethiye**
```
Photo location: /Volumes/LaCie Travel/Turkiye/Ege/İzmir/Çeşme/Alaçatı/Kelebekler_Vadisi/
Tags generated:
- kelebekler vadisi (location)
- fethiye (region)
- mavi (color dominant)
- dağ (landscape feature)
- vadi (geographic)
- tekne (if present)
- plaj (if present)
- sahil (if present)
- insan (if present)
- [sayı: 1, 3, 5] (people count)
- açık gökyüzü (weather)
- yağmur (if present)
- sis (if present)
- panoramik görünüm (composition)
```

**Example 2: Kekova, "Teknede Kemal Kaya" (with face recognition)**
```
Photo tags:
- Kekova (location)
- tekne (activity/object)
- mavi (color)
- deniz (landscape)
- insan (detected)
- açık hava (weather/setting)
- Kemal Kaya (FACE RECOGNITION - custom model trained on your photo)
```

### Budget Strategy
**$0 - Free Only**
- Claude API: Used for semantic understanding (tagged in budget tracking)
- OpenCV: Local face detection (free, open source)
- Custom face recognition: Train on Kemal Kaya photos → deploy locally
- No GPU acceleration (only i5 Mac CPU + optional server CPU)

### Timeline & Processing
**Two-Pass System:**

**Pass 1 - Quick Basic Tags (ALL 226K photos)**
- Extract location from path (Kelebekler Vadisi, Fethiye, etc.)
- Fast color detection (dominant color)
- Basic object detection (OpenCV cascade or lightweight model)
- Weather/conditions (sky, rain, fog, panorama)
- People count (face detection)
- Approximate time of day (image analysis)
- Expected time: ~30-50 hours (CPU-bound)

**Pass 2 - Deep Semantic Tags (Selected subset or all, depending on resources)**
- Claude Vision: narrative understanding, relationships, context
- Face recognition: Find all Kemal Kaya appearances
- Activity inference: "hiking", "market visit", "boat tour"
- Landmark identification: temples, beaches, historical sites
- Story tags: connects to guide narratives
- Expected time: ~200-300 hours (API-bound, ~5 photos/min with Claude)

**Total Timeline:** 230-350 hours (9-15 days continuous, or ~2-3 weeks part-time)

### Story Preservation & Deduplication
- **Strategy:** Keep MOST variants (loose threshold)
- **Deduplication threshold:** Hamming distance 8 (generous)
- **Result:** ~180-200K canonical photos (keep duplicates of important subjects)
- **Philosophy:** "Elder analysis insufficient now, monetize later with budget"
- **Future:** Manual review + smart deletion after editorial review

### Face Recognition (Custom)
**Goal:** Identify and tag all Kemal Kaya photos automatically

**Implementation:**
1. User provides 10-20 clear face photos of Kemal Kaya
2. Train simple face recognition model (OpenCV LBP faces or Dlib)
3. Scan all 226K photos for face matches
4. Tag matches with "Kemal Kaya" + confidence score
5. Allow manual review of uncertain matches

---

## Revised System Architecture

```
PHASE 0: PREPARATION
├─ Collect Kemal Kaya reference photos (10-20 clear face samples)
├─ Train face recognition model locally
└─ Extract location hierarchy from filesystem

PHASE 1: QUICK PASS (ALL 226K photos)
├─ Extract path-based location tags
├─ Color detection (dominant color)
├─ Object detection (fast cascades)
├─ Weather/condition detection
├─ People count + face detection
├─ Kemal Kaya identification
└─ Result: ~226K photos with basic tags (quick pass)

PHASE 2: DEDUPLICATION (Optional, for storage optimization)
├─ Compute perceptual hash (phash) for all 226K
├─ Group by similarity (Hamming distance ≤ 8)
├─ Keep: 1 best + variants of important subjects
└─ Result: ~180-200K canonical photos

PHASE 3: DEEP PASS (All or subset, depending on timeline)
├─ Claude Vision semantic understanding
├─ Activity & landmark inference
├─ Story narrative tags
├─ Relationship mapping (this photo connects to...)
└─ Result: Rich semantic metadata for all/subset

PHASE 4: EXPORT & UPLOAD
├─ Generate metadata JSON for each photo
├─ Optimize for WordPress metadata
├─ Upload to YO OS with tags
└─ Enable semantic search
```

---

## Required Implementation Components

### 1. **Path-Based Location Extraction** (NEW)
```python
/Volumes/LaCie Travel/Turkiye/Ege/İzmir/Çeşme/Alaçatı/
  → tags: ["alaçatı", "çeşme", "izmir", "ege", "turkiye"]

/Volumes/LaCie Travel/Turkiye/Akdeniz/Muğla/Kekova/
  → tags: ["kekova", "muğla", "akdeniz", "turkiye"]
```

### 2. **Face Recognition Model (NEW)**
```python
# Train on Kemal Kaya references
kemal_faces = load_reference_photos("kemal_kaya_*.jpg")  # 10-20 samples
face_model = train_face_recognizer(kemal_faces)

# Scan all 226K for matches
for photo in all_photos:
    faces_detected = detect_faces(photo)
    for face in faces_detected:
        confidence = face_model.match(face, kemal_faces)
        if confidence > 0.85:
            tag_as("Kemal Kaya", confidence)
```

### 3. **Quick Pass Tagger (NEW - Fast, Local)**
```python
# For each photo:
# 1. Extract path → location tags
# 2. Color detection (OpenCV)
# 3. Face count + Kemal match
# 4. Weather/sky detection
# 5. Panorama detection (aspect ratio)
# Store: basic_tags JSON
```

### 4. **Deep Pass Tagger (Existing - Claude Vision)**
```python
# Takes basic_tags + image
# Claude Vision generates:
# - Activity ("hiking", "market", "boat tour")
# - Landmark identification
# - Relationships ("this connects to...")
# - Story narrative
# Store: semantic_tags JSON
```

### 5. **Perceptual Hash & Deduplication (Existing, but LOOSE)**
```python
# Hamming distance 8 (not 5 - keep more variants)
# Keep: best of similar photos + any unique subjects
# Result: ~180-200K from 226K
```

---

## Data Model (Updated)

```sql
asset_index (226K rows)
├── location_tags TEXT       -- Path-based: ["alaçatı", "çeşme", "izmir"]
├── color_dominant TEXT      -- Fast detection: "blue", "green", "orange"
├── objects_detected TEXT    -- OpenCV: ["person", "boat", "mountain"]
├── people_count INT         -- Face count: 1, 2, 5, etc.
├── kemal_kaya_confidence REAL -- 0-1, face match confidence
├── weather_conditions TEXT  -- ["sunny", "clear_sky", "open_air"]
├── composition TEXT         -- ["panoramic", "landscape", "portrait"]
├── basic_tags_json TEXT     -- Pass 1 output (quick)
├── semantic_tags_json TEXT  -- Pass 2 output (deep)
├── perceptual_hash TEXT     -- For deduplication
└── canonical BOOLEAN        -- Keep this variant? (after dedup)
```

---

## User Story Examples

### Story 1: Find all Kemal Kaya beach photos
```
SELECT * FROM asset_index 
WHERE kemal_kaya_confidence > 0.85 
  AND location_tags LIKE '%beach%' OR '%sahil%' OR '%plaj%'
  AND color_dominant = 'blue'
ORDER BY selection_score DESC
```

### Story 2: Kekova collection (all variants)
```
SELECT * FROM asset_index 
WHERE location_tags LIKE '%kekova%'
  AND canonical = TRUE
ORDER BY quality_score DESC
```

### Story 3: Butterfly Valley unique shots
```
SELECT * FROM asset_index 
WHERE location_tags LIKE '%kelebekler vadisi%'
  AND people_count IS NOT NULL
ORDER BY composition
```

---

## Technical Constraints & Solutions

| Constraint | Solution |
|-----------|----------|
| **No GPU** (only i5 Mac) | Phase 1 local-only (fast), Phase 2 async Claude API |
| **$0 budget** | Claude API tracked separately (not project cost), OpenCV free |
| **226K photos** | 2-pass system: quick pass ALL, deep pass selective/async |
| **No Mac Photos ML** | Custom face recognition (Kemal Kaya), Claude Vision for semantics |
| **CPU bound on Mac** | Optional: offload Phase 1 to server (CPU also available there) |

---

## Implementation Roadmap (for Sonnet)

1. **Design Phase:**
   - [ ] Define location taxonomy from filesystem
   - [ ] Design face recognition training pipeline
   - [ ] Spec basic_tags schema vs semantic_tags schema
   - [ ] Design deduplication strategy (Hamming distance 8)

2. **Phase 1 Implementation (Quick Pass):**
   - [ ] Path-based location tag extraction
   - [ ] Color dominant detection (OpenCV)
   - [ ] Face detection + count
   - [ ] Kemal Kaya face recognition training & deployment
   - [ ] Weather/sky/panorama detection
   - [ ] Batch process all 226K → store basic_tags

3. **Phase 2 Setup (Deep Pass):**
   - [ ] Refactor Claude Vision tagger for narrative focus
   - [ ] Remove complex hierarchy, add location-aware prompts
   - [ ] Queue system for async processing
   - [ ] Landmark identification module

4. **Deduplication (Optional):**
   - [ ] Compute phash for all 226K
   - [ ] Group by Hamming distance ≤ 8
   - [ ] Score and select canonical photos
   - [ ] Result: ~180-200K kept

5. **Export & Integration:**
   - [ ] Generate metadata JSONs
   - [ ] WordPress integration
   - [ ] Semantic search API

---

## Questions for Sonnet

1. **Face Recognition Model:** Use OpenCV's LBP faces (simple, local) or Dlib (better but slower)? Train on Mac or move to server?

2. **Path Extraction:** Automatically parse folder structure (Turkiye/Ege/İzmir/...) into hierarchy, or need manual mapping?

3. **Phase 1 vs Phase 2:** Should Phase 1 process ALL 226K? (Yes, seems like it) Should Phase 2 process all or just highest-quality subset?

4. **Deduplication timing:** Before Phase 2 (deduplicate then tag 180K) or after Phase 2 (tag all 226K then deduplicate)?

5. **Server Migration:** Phase 1 can run on Mac (local, CPU-bound). Should we plan to move to server for Phase 2 (API-bound, can parallelize)?

6. **Kemal Kaya Reference:** How many clear face photos to train on? (Suggest 10-20?) Will you provide them?

---

## Success Criteria (Revised)

✅ All 226K photos indexed with basic tags (location, color, objects, people count)  
✅ All 226K scanned for Kemal Kaya face recognition  
✅ Kemal Kaya photos tagged with high confidence (>0.85)  
✅ Loose deduplication applied (180-200K canonical kept)  
✅ All/most tagged with semantic metadata (activity, narrative, landmarks)  
✅ "Kelebekler Vadisi insanlar var mı" → correct results  
✅ "Kemal Kaya teknede resimler" → Kemal Kaya-tagged boat photos  
✅ Ready for WordPress upload with full metadata  

---

## Why This Approach is Better

✅ **Two-pass:** Fast basic metadata immediately, deep understanding later  
✅ **Location-aware:** Filesystem structure leveraged for automatic tagging  
✅ **Face recognition:** Personal narrative (Kemal Kaya identification)  
✅ **Loose dedup:** Keep story variants, not just "best of duplicates"  
✅ **$0 budget:** Free tools only, no API costs upfront  
✅ **Scalable:** Phase 1 can run on any machine, Phase 2 async via API  
✅ **Narrative-focused:** Tags tell STORY, not just what's in the photo  

