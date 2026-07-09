# Runbook

Day-to-day operations for Pictovap.

## Attach Images to a Post

```bash
# Single post, default settings
pictova attach --site yoldaolmak --post 265713

# With count and people preference
pictova attach --site yoldaolmak --post 265713 --count 4 --people-first

# Preview only — no WordPress changes
pictova plan --site yoldaolmak --post 265713 --count 4 --people-first
```

## Check System Health

```bash
pictova health
```

```bash
# With visual memory check
python3 - <<'PY'
from src.main import search_semantic_assets
results = search_semantic_assets('test', count=3)
print(f"Visual memory: {len(results)} results found")
PY
```

## Run Tests

```bash
python3 -m pytest -q
```

Expected: all passed, 0 failures.

## Start HTTP Server

```bash
pictova serve --host 127.0.0.1 --port 8040 &

# Verify
curl -s http://127.0.0.1:8040/health
```

## Submit Async Job

```bash
curl -s -X POST http://127.0.0.1:8040/jobs/attach \
  -H 'Content-Type: application/json' \
  -d '{"site":"yoldaolmak","post_id":265713,"count":4,"people_first":true}'
```

Returns `{"job_id":"abc123","status":"pending"}`.

## Poll Job Status

```bash
curl -s http://127.0.0.1:8040/jobs/abc123
```

Poll until `"status"` is `"completed"` or `"failed"`.

## List All Jobs

```bash
curl -s http://127.0.0.1:8040/jobs
```

## Re-index Visual Memory

Run after importing new photos:

```bash
cd /Users/username/Projects/Pictova
./.venv/bin/python index_memory_daily.py --mode photos --daily-limit 100
./.venv/bin/python extract_apple_photos_ml.py
```

See [Indexing](indexing.md) for full details.

## Common Issues

**`attach` fails with "No candidates found"**
1. Run `pictova plan` to see if any candidates are returned
2. Check `YO_VISUAL_MEMORY_DB` is set and points to a populated database
3. Check `UNSPLASH_ACCESS_KEY` is valid
4. Check the post has readable content (not empty)

**`attach` fails with auth error**
1. Verify `WP_USER` and `WP_PASSWORD` in `.env`
2. Verify the Application Password is still active in WordPress admin
3. Verify the user has Editor permissions

**`plan` returns candidates but `process` rejects all**
- Quality gate is blocking — images are blurry or wrong aspect ratio
- Try `--source unsplash` for a different pool of candidates
- Lower `MIN_QUALITY_SCORE` in the site profile temporarily

## Financial Controls & Limits

**CRITICAL RULE: PERMANENT BAN ON PAID GEMINI API USAGE.**
- We absolutely do not use the paid Gemini API.
- The primary (first) Gemini API key must only be run up to exactly 90% of the free budget (1,350 requests per day out of the 1,500 free limit).
- `fast_scan.py` is hardcoded to halt execution if the daily scanned items exceed 1,350 to prevent accidental billing.
