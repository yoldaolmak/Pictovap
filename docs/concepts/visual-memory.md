# Visual Memory

Visual Memory is Pictova's local image index. It is a SQLite database that stores metadata about every image in your library — including Apple Photos ML enrichments — and powers the semantic selection engine.

## What It Contains

Each record in the `asset_index` table represents one image and stores:

| Field | Description |
|-------|-------------|
| `source_path` | Absolute path to the original file |
| `filename` | File name |
| `title` | Human-readable title (from Photos or inferred) |
| `description` | Generated or Photos-sourced description |
| `summary` | Short text summary |
| `location` | Place name where the photo was taken |
| `city` | City extracted from Photos moment metadata |
| `country` | Country |
| `activity` | Activity detected (hiking, dining, etc.) |
| `scene` | Scene type (landscape, street, interior, etc.) |
| `quality_score` | Composite score: sharpness, exposure, composition |
| `face_count` | Number of faces detected (Apple ML) |
| `blur_score` | Apple Photos blur indicator |

## Why It Exists

Mac Photos stores originals with UUID-based paths that change across devices and library migrations. A path-only approach breaks silently. Visual Memory solves this by indexing semantic fields alongside paths, so the selection engine can match on `city`, `scene`, or `activity` even when the path structure is opaque.

## The Two Runtimes

Visual Memory operates across two runtimes:

**Index Runtime** (separate, in `/Users/yoldaolmak/Projects/Pictova`):
- Scans Photos originals
- Applies quality gate
- Reads Apple Photos `.sqlite` for ML metadata
- Writes to `visual_memory.db`

**Consumer Runtime** (this repo, Pictova):
- Reads `visual_memory.db` via `YO_VISUAL_MEMORY_DB`
- Uses the index for semantic selection
- Never writes to the index

This separation keeps the indexer and the selection engine independently deployable.

## Indexing

```bash
cd /Users/yoldaolmak/Projects/Pictova
./.venv/bin/python index_memory_daily.py --mode photos --daily-limit 0
./.venv/bin/python extract_apple_photos_ml.py
```

The first command discovers and quality-gates originals. The second enriches indexed records with Apple ML metadata (moment, location, faces, blur/exposure scores).

Run both after importing new photos or on a daily schedule.

See: [Indexing Ops Guide](../ops/indexing.md)

## Verification

```python
from src.main import search_semantic_assets
print(search_semantic_assets('Sinop', count=5))
```

A working index returns real file paths to Photos originals matching the query. An empty result means the index is missing, the `YO_VISUAL_MEMORY_DB` env var is unset, or no assets match.
