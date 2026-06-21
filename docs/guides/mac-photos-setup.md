# Mac Photos Setup

Pictova can use your Mac Photos library as an image source. This guide covers indexing your library and connecting it to Pictova.

## How It Works

1. A separate index runtime scans your Photos originals
2. Apple's on-device ML metadata (location, scene, faces) is extracted
3. All metadata is written to a SQLite database (`visual_memory.db`)
4. Pictova reads this database via `YO_VISUAL_MEMORY_DB`

The index runtime and Pictova are intentionally separate: the indexer runs on your Mac, Pictova can run anywhere.

## Step 1: Set Up the Index Runtime

The index runtime lives in a separate directory (not this repo):

```bash
cd /Users/yoldaolmak/Downloads/YO_OS_VIL
```

If you don't have this directory, contact the project maintainer or set up the indexer from the `ops/` directory in this repo.

Verify the runtime's Python environment:

```bash
./.venv/bin/python -V
# Python 3.9.x or 3.10.x
```

## Step 2: Index Your Photos Library

```bash
./.venv/bin/python index_memory_daily.py --mode photos --daily-limit 0
```

`--daily-limit 0` means: index everything, no cap. For subsequent runs, set `--daily-limit 100` to only process new additions.

This step:
- Discovers Photos originals via the Photos library database
- Applies the quality gate (sharpness, exposure, resolution)
- Writes qualifying assets to `asset_index`

Expected output: discovered N, kept M (kept < discovered due to quality gate).

## Step 3: Enrich with Apple ML Metadata

```bash
./.venv/bin/python extract_apple_photos_ml.py
```

This reads Apple's internal `Photos.sqlite` and enriches indexed assets with:
- GPS location → city and country via reverse geocoding
- Moment title → location string
- Face detection count
- Blur score, exposure classification

This step may take several minutes for large libraries.

## Step 4: Connect to Pictova

In Pictova's `.env`:

```bash
YO_VISUAL_MEMORY_DB=/Users/yoldaolmak/Downloads/YO_OS_VIL/data/visual_memory.db
```

## Step 5: Verify

```bash
python3 - <<'PY'
from src.main import search_semantic_assets
results = search_semantic_assets('Sinop', count=5)
for r in results:
    print(r['source_path'])
PY
```

If you see real file paths to your Photos originals, the connection is working.

## Keeping the Index Fresh

After importing new photos:

```bash
cd /path/to/YO_OS_VIL
./.venv/bin/python index_memory_daily.py --mode photos --daily-limit 100
./.venv/bin/python extract_apple_photos_ml.py
```

Or automate with a daily cron job. See [Indexing Ops](../ops/indexing.md).

## Notes

- Photos originals must be downloaded to disk (not "Optimize Mac Storage")
- iCloud Photos in "optimized" mode will show thumbnails in the index but fail at processing time
- The indexer does not modify your Photos library in any way
