# The Pipeline

Every Pictova attach operation runs through the same four-stage pipeline. You can enter at any stage, inspect the output, and decide whether to continue.

## Stages

```
review → plan → process → attach
```

### 1. review

Reads the post from WordPress and returns its context without touching any images.

```bash
pictova review --site yoldaolmak --post 265713
```

Output includes: title, excerpt, derived location query, derived topic, category and tag list, current image count in the post.

Use this to verify Pictova is reading the post correctly before committing to image selection.

### 2. plan

Queries all configured sources and returns the candidate image list without downloading or processing anything.

```bash
pictova plan --site yoldaolmak --post 265713 --count 4 --people-first
```

Output includes: each candidate asset path or URL, its source, its semantic score, its quality score, and any flags (face detected, aspect ratio match, etc.).

Use this to verify the selection logic before spending time on processing.

### 3. process

Downloads and processes the selected images — resizing, format conversion, watermark removal — without publishing to WordPress.

```bash
pictova process --site yoldaolmak --post 265713 --count 4 --people-first
```

Output includes: processed file paths, dimensions, quality gate result, any rejected assets and why.

Use this to verify image quality and processing output before upload.

### 4. attach

Runs the full pipeline: review + plan + process + upload to WordPress + insert Gutenberg blocks.

```bash
pictova attach --site yoldaolmak --post 265713 --count 4 --people-first
```

Output is a structured JSON contract:

```json
{
  "site": "yoldaolmak",
  "post_id": 265713,
  "selected_assets": [...],
  "rejected_assets": [...],
  "uploaded_media_ids": [101, 102, 103, 104],
  "inserted_blocks": [...],
  "warnings": [],
  "duration_ms": 4210
}
```

## Engine Paths

Two engine implementations exist:

- **Legacy** (default): wraps the existing orchestrator. Battle-tested, richer semantic metadata.
- **Native** (`--engine native`): built entirely on `src/pictova/engine/*`. Cleaner architecture, in active development.

```bash
pictova attach --site yoldaolmak --post 265713 --count 4 --engine native
```

See [Native vs Legacy Engine](../architecture/native-vs-legacy.md) for the full comparison.

## Async Jobs (HTTP)

When running as an HTTP service, `attach` is a long-running operation. Use the async job endpoint instead of the synchronous attach endpoint:

```bash
# Start job
curl -X POST http://127.0.0.1:8040/jobs/attach \
  -H 'Content-Type: application/json' \
  -d '{"site":"yoldaolmak","post_id":265713,"count":4,"people_first":true}'

# Returns: {"job_id": "abc123", "status": "pending"}

# Poll for result
curl http://127.0.0.1:8040/jobs/abc123
```

See [HTTP API Reference](../reference/http-api.md) for full job lifecycle details.
