# YOOS-VIL

> **Visual Intelligence Layer** — AI-powered photo indexing, semantic tagging, and media publishing for [yoldaolmak.com](https://yoldaolmak.com)

A system that transforms 200,000+ raw travel photos into a structured, searchable media library — enriched with semantic metadata and published directly to WordPress.

---

## What This Is

YOOS-VIL is the visual asset backbone of a travel publication running since 2011. It is not a generic image gallery or photo management tool.

It is a two-pass AI pipeline that:

1. **Indexes** photos from local archives and external HDD (200,000+ assets)
2. **Enriches** each photo with semantic tags, location context, and activity inference
3. **Identifies** the author (face recognition via custom-trained model)
4. **Selects** best candidates per article section using semantic slot planning
5. **Publishes** optimized images directly to WordPress with correct metadata

---

## Architecture

```
YOOS-VIL/
├── yo_phase1_quick_tagger.py     # Fast local pass: location, color, face detection
├── extract_kemal_kaya_faces.py   # Face recognition model training + scan
├── yo_semantic_tagger.py         # Deep semantic tagging via Claude Vision
├── yo_image_processor.py         # Crop, resize, format conversion
├── yo_wp_uploader.py             # WordPress media library upload
├── yo_orchestrator.py            # End-to-end pipeline runner
├── index_memory_daily.py         # Incremental daily index update
├── run_deposit.py                # Depositphotos licensed asset fetcher
└── data/
    └── visual_memory.db          # SQLite asset index (semantic + EXIF)
```

---

## Pipeline

```
HDD Archive (200,000+ photos)
    ↓
Phase 1 — Quick Pass (local, CPU)
    ├── Path-based location extraction
    ├── Dominant color detection (OpenCV)
    ├── Face detection + Kemal Kaya identification
    └── Perceptual hash deduplication
    ↓
Phase 2 — Deep Pass (async, Claude Vision)
    ├── Scene and activity inference
    ├── Landmark identification
    └── Story narrative tags
    ↓
Slot Planning
    ├── Match photos to article H2/H3 sections
    └── Select best candidate per slot
    ↓
WordPress Upload
    ├── WebP conversion + crop
    ├── Alt text and caption generation
    └── REST API publish
```

---

## Key Capabilities

| Capability | Details |
|---|---|
| **Face recognition** | Custom-trained model identifies the author across 200,000+ photos |
| **Semantic tagging** | Location, scene, activity, landmark, and story tags per image |
| **Slot planning** | Matches images to article sections by semantic relevance |
| **Deduplication** | Perceptual hash with configurable Hamming threshold |
| **Licensed assets** | Depositphotos API integration for gap-filling |
| **Daily indexing** | Incremental scan keeps the library current |

---

## Stack

- **Python 3.10** — core engine
- **OpenCV + dlib** — local face detection and recognition
- **Claude Vision** — deep semantic enrichment
- **SQLite** — visual memory database (FTS search enabled)
- **WordPress REST API** — media publishing
- **Depositphotos API** — licensed stock asset fallback

---

## Related

- **[YOOS-APP](https://github.com/yoldaolmak/YOOS-APP)** — editorial content engine
- **[yoldaolmak.com](https://yoldaolmak.com)** — live publication
