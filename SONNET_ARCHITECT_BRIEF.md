# YO_OS_VIL Semantic Tagging System — Architecture Brief for Claude Sonnet

## Executive Summary

Building a Depositphotos-quality semantic tagging system for 226K+ travel photos (Canon 60D HDD archive). **Critical insight discovered:** System was filtering photos incorrectly (226K → 600 = 0.26%), but actual requirement is **deduplication + story preservation** (should yield ~180-200K = 80-90% of originals).

Need architectural redesign from **"elim ve seç"** (filter & select) to **"deduplicate ve hikaye tut"** (deduplicate & preserve stories).

---

## User Requirements Timeline

### Phase 1: Analysis & Optimization (Apr 15, 2026)
**User Request:** "Analiz et, VIL analizi yap. Sistem iyi mi nasıl geliştirilir?"
- Initial system analysis revealed: indexing stalled, metadata broken, GCV budget unrealistic (10+ years)
- **Action taken:** Identified bottlenecks, proposed semantic tagging alternative

### Phase 2: Emergency Pipeline Fix (Apr 15-16, 2026)
**User Request:** "Token optimizasyonu yap, acil pipeline çalışır hale getir. GCV %80 cap, naming/metadata fixes, soru sorma"
- Fixed metadata generator (model IDs, Turkish char handling, confidence defaults)
- Added resilient daemon for HDD indexing (mount checks, auto-restart)
- Implemented GCV budget capping (800/month = %80 of free tier)
- **Key constraint:** No approval-asking, batch all operations

### Phase 3: Semantic Foundation (Apr 16-17, 2026)
**User Request:** "Semantik yaklaşılmalı: scene/objects/time_of_day/location. Bunu anla, bir şey yapma bekle"
- Recognized that GCV alone won't work (10+ years at 26 photos/day)
- Proposed semantic tagging using Apple's free ML + CLIP + OpenCV
- Established tag taxonomy (Depositphotos-aligned)
- **Key insight:** "Benden onay almadan işlemler için yes/no sormadan"

### Phase 4: Semantic Tagging Implementation (Apr 17-20, 2026)
**User Requests:**
1. "Başka yöntemlerle bedava... Nasıl yapıldı?" → Revealed prior Codex approach used Apple Photos native ML + photo_candidates.sqlite
2. Build comprehensive semantic tagger
3. Enable semantic search: "madura adası 5 foto insanlar" → correct results

**Implementation:**
- Claude Vision semantic tagger (`yo_semantic_tagger.py`)
- Hierarchical tag taxonomy (`yo_tag_taxonomy.py`)
- Semantic search engine (`yo_semantic_search.py`)
- Face detection system (`yo_face_detector.py`)
- Quality/duplicate detection (`yo_quality_comparison.py`)
- Pipeline coordinator (`yo_full_tagger_pipeline.py`)

**Current Status:** 50/600 photos tagged (8.3%), ~55h ETA at 10 photos/min

### Phase 5: Critical Re-evaluation (TODAY - Apr 20, 2026)
**User Statement:** "Total HDD Fotoğraf 600 bu ne demek? YANLIŞ! 226K'dan 600 iyi = sistem çökmüş. %80-90 kullanılabilir, amaç eleme değil en iyisini almak"

**CRITICAL REALIZATION:**
- System was filtering too aggressively (226K → 600 = 0.26%)
- **Real requirement:** %80-90 of photos are usable = ~180-200K photos
- **True goal:** NOT to eliminate bad photos, but to:
  1. Find duplicates (same scene, multiple shots) → keep BEST of each group
  2. Preserve unique stories (even low-quality) if they tell a good story
  3. Process all selected photos (180-200K) to Depositphotos quality
  4. Penetrate into YO OS with guide-compliant images

---

## Project Objectives (Corrected)

| Objective | Previous Understanding | Corrected Understanding |
|-----------|------------------------|------------------------|
| **Input Volume** | 226K photos | 226K photos ✓ |
| **Selection Ratio** | 0.26% (600 photos) = BROKEN | 80-90% (180-200K) = natural diversity |
| **Selection Logic** | Quality filtering | Deduplication + story preservation |
| **Processing Goal** | Process "good" 600 | Process ~180-200K unique/best variants |
| **Upload Target** | 600 to WordPress | 180-200K to WordPress (with story-based selection) |
| **Use Case** | Generic travel photos | YO OS guide-aligned narratives |

---

## Current Architecture (Needs Redesign)

### ✅ What's Built

1. **Semantic Tagging Pipeline**
   - Claude Vision: scene, objects, activity, location, time, mood, lighting, weather, color
   - Confidence scores (0.55-0.99), detailed descriptions
   - Stores in: scene_ml, objects_json, time_of_day, location_specifics

2. **Hierarchical Tag Taxonomy**
   - 5 categories, Turkish/English aliases
   - Per-tag confidence thresholds
   - Sub-tags and relationships

3. **Semantic Search**
   - Location-based path matching + tag matching
   - AND/OR logic for tag combinations
   - Example: "madura adası" + ["island", "ocean"] → photos

4. **Face Detection** (ready but not executed)
   - OpenCV Haar Cascades
   - Gender/age estimation
   - Bounding boxes

5. **Quality/Duplicate Detection** (ready but not executed)
   - Perceptual hashing (phash) for duplicates
   - Quality scoring (sharpness, composition, lighting, color)
   - Duplicate grouping and best selection

### ❌ Current Problems

1. **Pre-filtering broken**: 226K → 600 (0.26%) - should be 80-90%
2. **Selection logic wrong**: Filters by quality, not by uniqueness
3. **Scope misunderstood**: Thought task was "find good photos", actually "find unique stories + best variants of duplicates"
4. **Processing scope wrong**: Planning to process 600, should plan for 180-200K
5. **No deduplication yet**: Need perceptual hash to identify duplicate groups first

---

## What Needs Redesign

### 1. **Indexing Phase** (BROKEN)
```
Current:  226K → [quality filter] → 600
Needed:   226K → [index ALL] → [tag ALL]
```

**Action:** Don't filter during indexing. Index everything.

### 2. **Deduplication Phase** (MISSING)
```
Step 1: Compute perceptual hash for all 226K
Step 2: Group by phash similarity (Hamming distance ≤ 5 = duplicates)
Step 3: For each group: keep BEST (sharpness, composition, lighting)
Step 4: Result: ~180-200K unique/best photos
```

### 3. **Semantic Tagging Phase** (SCOPE WRONG)
```
Current:  Tag 600 photos (too small)
Needed:   Tag 180-200K photos (deduplicated set)
```

### 4. **Story Preservation Logic** (MISSING)
```
Quality scoring should ALSO consider:
- Is this a unique story/location/activity?
- Does this image tell narrative even if technically imperfect?
- Multiple angles of same scene = keep 1-2 best, not just 1

Example: "Badly lit fish market" = keep despite poor exposure,
         if no other "fish market" photos exist
```

---

## Database Schema (Current)

```sql
asset_index (600 rows currently, should be 226K)
├── scene_ml TEXT              -- Claude Vision scenes
├── objects_json TEXT          -- Claude Vision objects + faces
├── time_of_day TEXT           -- Time tags
├── location_specifics TEXT    -- Location/mood/lighting/weather
├── apple_blur_score REAL      -- Mac Photos ML (if available)
├── apple_exposure_score REAL  -- Mac Photos ML (if available)
├── perceptual_hash TEXT       -- NOT YET COMPUTED (needs this)
└── quality_score REAL         -- Existing, but used wrong
```

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Vision Tagger | ✅ Working | 50/600 tagged, 0.77-0.80 confidence |
| Tag Taxonomy | ✅ Ready | Hierarchical, Turkish/English |
| Semantic Search | ✅ Ready | Can search tagged photos now |
| Face Detection | ✅ Ready | Not executed (OpenCV ready) |
| Duplicate Detection | ✅ Ready | Not executed (phash ready) |
| **Redesigned flow** | ❌ Missing | THIS IS WHAT'S NEEDED |

---

## What's Blocking Progress

1. **Misunderstanding of scope:** Was filtering 226K to 600, but should process 80-90%
2. **Wrong order of operations:** Tagging THEN deduplicating, should deduplicate FIRST
3. **Story preservation logic:** No mechanism to identify "unique stories" vs. "duplicates"
4. **Processing capacity:** Was planning 600 photos, should plan 180-200K

---

## Recommended Architectural Flow (for Sonnet)

```
1. SCAN & INDEX (all 226K, minimal processing)
   └─ Extract: filename, path, size, creation_date, basic EXIF
   └─ Compute: perceptual_hash (phash)
   
2. DEDUPLICATE (group similar photos)
   └─ Group by phash (Hamming distance ≤ 5)
   └─ Score each group member (sharpness, composition, lighting, color)
   └─ Keep: BEST of each group + any unique story photos
   └─ Result: ~180-200K "canonical" photos
   
3. SEMANTIC TAG (all 180-200K)
   └─ Claude Vision: scene, objects, activity, location, time, mood
   └─ Face detection: people, emotions, demographics
   └─ Location parsing: extract city/region/landmark
   └─ Quality scoring: technical quality + story quality
   
4. SEARCH & FILTER (enable queries)
   └─ "madura adası 5 foto insanlar" → semantic + location match
   └─ Tag suggestions for regions
   └─ Quality-based ranking
   
5. EXPORT TO WORDPRESS (180-200K images)
   └─ Resize + optimize
   └─ Embed metadata
   └─ Upload with guide-compliance checking
```

---

## Questions for Sonnet

1. **Deduplication strategy:** Perceptual hash (phash) with Hamming distance threshold, or should we also use metadata matching (same location + time + similar EXIF)?

2. **Story preservation:** How to identify "unique stories" vs. "duplicates"? Should we:
   - Use semantic tags (different scene/activity = unique)?
   - Use location diversity (different region = keep all)?
   - Manual review of groups with questionable uniqueness?

3. **Processing order:** Should we:
   - Deduplicate FIRST (226K → 180-200K), then tag?
   - Or tag ALL 226K, then deduplicate based on tags?

4. **Quality scoring:** Should quality score balance:
   - Technical quality (sharpness, composition, lighting)?
   - Narrative quality (does it tell a story)?
   - Location uniqueness (how common is this location in dataset)?

5. **Timeline:** With 180-200K photos to process and ~10 photos/min (Claude Vision API), ETA is ~300-400 hours (~2-3 weeks). Is this acceptable, or should we batch with GPU acceleration?

6. **Story tagging:** Beyond semantic tags, should we add:
   - Narrative metadata ("what happened here")?
   - Contextual tags ("this completes the X story")?
   - Author notes ("why this photo matters")?

---

## User Constraints

- ✅ **Bedava** (free) - only Claude API cost
- ✅ **No approval asking** - batch operations, run autonomously
- ✅ **Mac-native preferred** - leverage Apple ML when available
- ✅ **Depositphotos quality** - comprehensive semantic tagging
- ✅ **Turkish-aware** - tag aliases, location names
- ⚠️ **226K photos is significant** - need efficient deduplication strategy
- ⚠️ **Story preservation is critical** - not just "good vs. bad", but "unique vs. duplicate"

---

## Files Involved

- `/Users/KemalKaya/YO_OS_VIL/yo_semantic_tagger.py` - Claude Vision tagger (ready)
- `/Users/KemalKaya/YO_OS_VIL/yo_tag_taxonomy.py` - Tag hierarchy (ready)
- `/Users/KemalKaya/YO_OS_VIL/yo_semantic_search.py` - Search engine (ready)
- `/Users/KemalKaya/YO_OS_VIL/yo_face_detector.py` - Face detection (ready)
- `/Users/KemalKaya/YO_OS_VIL/yo_quality_comparison.py` - Deduplication (ready but needs redesign)
- `/Users/KemalKaya/YO_OS_VIL/index_vil.py` - HDD indexing (NEEDS FIX)
- `/Users/KemalKaya/YO_OS_VIL/visual_memory/db.py` - Database schema (ready)
- `/Users/KemalKaya/YO_OS_VIL/yo_orchestrator.py` - Pipeline orchestration (needs redesign)

---

## Success Criteria

✅ All 226K photos indexed  
✅ Perceptual hashes computed  
✅ Duplicate groups identified  
✅ Best-of-group selected  
✅ Unique stories preserved  
✅ ~180-200K canonical photos identified  
✅ All 180-200K tagged with semantic metadata  
✅ "madura adası 5 foto insanlar" → correct results  
✅ All processed photos meet YO OS guide requirements  
✅ Uploaded to WordPress with proper metadata  

---

## For Sonnet

Please review and provide:
1. **Architecture redesign** - correct order of operations
2. **Deduplication algorithm** - optimal strategy for 226K photos
3. **Story preservation logic** - how to identify and keep unique narratives
4. **Processing timeline** - realistic ETA with constraints
5. **Implementation roadmap** - which files to modify, in what order
6. **Risk mitigation** - what could go wrong, how to handle it

This is a semantic/architectural problem, not a coding problem. User wants system that respects "even bad photo with good story > perfect duplicate".
