# Indexing

Visual Memory index maintenance guide.

## Index Location

```
/Users/yoldaolmak/Projects/Pictovap/
  data/
    visual_memory.db     ← the index
  index_memory_daily.py
  extract_apple_photos_ml.py
  .venv/
```

## What the Index Contains

The `asset_index` table. One row per image. Key fields:

- `source_path` — absolute path to original
- `location`, `city`, `country` — from Photos moment metadata
- `scene`, `activity` — from Apple ML
- `quality_score` — composite (sharpness + exposure + resolution)
- `face_count` — from Apple face detection
- `blur_score` — Apple blur indicator

## Running the Indexer

### Full index (first time or after large import)

```bash
cd /Users/yoldaolmak/Projects/Pictova
./.venv/bin/python index_memory_daily.py --mode photos --daily-limit 0
./.venv/bin/python extract_apple_photos_ml.py
```

`--daily-limit 0` = no cap. May take 10–30 minutes for large libraries.

### Incremental update (after new photos)

```bash
./.venv/bin/python index_memory_daily.py --mode photos --daily-limit 100
./.venv/bin/python extract_apple_photos_ml.py
```

### Verify index health

```bash
python3 - <<'PY'
import sqlite3
db = "/Users/yoldaolmak/Projects/Pictovap/data/visual_memory.db"
con = sqlite3.connect(db)
count = con.execute("SELECT COUNT(*) FROM asset_index").fetchone()[0]
with_location = con.execute("SELECT COUNT(*) FROM asset_index WHERE city IS NOT NULL").fetchone()[0]
print(f"Total assets: {count}")
print(f"With location: {with_location}")
PY
```

## Quality Gate

The indexer applies a quality gate before writing to the index. An image is indexed only if:

- Width ≥ 1200px OR height ≥ 800px
- Not classified as blurry by Apple ML
- Not severely under or over-exposed

Images failing the gate are counted as "discovered but not kept" in the indexer output.

## Scheduling

To keep the index fresh automatically, add a daily cron job on your Mac:

```bash
# Edit crontab
crontab -e

# Add (runs at 3am daily)
0 3 * * * cd /Users/yoldaolmak/Projects/Pictovap && ./.venv/bin/python index_memory_daily.py --mode photos --daily-limit 200 >> /tmp/pictova-index.log 2>&1
```

Note: Mac must be awake and Photos library accessible at run time.

## Rebuilding the Index

If the index is corrupt or you want a clean slate:

```bash
cd /Users/yoldaolmak/Projects/Pictova
rm data/visual_memory.db
./.venv/bin/python index_memory_daily.py --mode photos --daily-limit 0
./.venv/bin/python extract_apple_photos_ml.py
```
