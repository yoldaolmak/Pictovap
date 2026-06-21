# Monitoring

## Health Check

```bash
pictova health
```

```bash
# Via HTTP
curl -s http://127.0.0.1:8040/health
```

Expected: `{"status":"ok","service":"pictova"}`

If this fails: check that `pictova serve` is running and the port is correct.

## Visual Memory Status

```bash
python3 - <<'PY'
from src.main import search_semantic_assets
r = search_semantic_assets('Istanbul', count=3)
print(f"Status: {'ok' if r else 'no results — check YO_VISUAL_MEMORY_DB'}")
PY
```

## Test Suite

```bash
python3 -m pytest -q
```

Run after any code change. All tests should pass. A failing test in CI means something in the engine contract changed.

## Job Queue Health (HTTP mode)

```bash
curl -s http://127.0.0.1:8040/jobs | python3 -m json.tool
```

Check for jobs stuck in `running` state for more than 5 minutes — this indicates a processing hang.

## Ops Health Script

```bash
python3 ops/yoos_vil_health.py
```

This script checks:
- Import paths
- Visual memory DB connectivity
- WordPress credential format validity
- Source driver availability

## What to Watch

| Signal | Normal | Investigate if |
|--------|--------|----------------|
| `attach` duration | 2–8 seconds | > 30 seconds |
| Quality gate rejection rate | 0–30% | > 70% consistently |
| Visual memory query results | ≥ 3 for any Turkish city | 0 for major cities |
| Test suite | All passed | Any failure |

## Logs

Pictova does not write structured logs yet (planned in Milestone A). Current output goes to stdout/stderr. Capture with:

```bash
pictova attach --site yoldaolmak --post 265713 2>&1 | tee /tmp/pictova-run.log
```
