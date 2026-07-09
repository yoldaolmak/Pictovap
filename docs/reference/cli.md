# CLI Reference

All Pictovap operations are available via the `pictova` command.

## Global Usage

```
pictova <command> [options]
```

## Commands

### `pictova health`

Check that the service is running and configured correctly.

```bash
pictova health
```

```json
{"status": "ok", "service": "pictova"}
```

No options.

---

### `pictova review`

Read a post from WordPress and display its derived context. Does not touch images.

```bash
pictova review --site <site> --post <post_id>
```

| Flag | Required | Description |
|------|----------|-------------|
| `--site` | Yes | Site profile name (e.g., `yoldaolmak`) |
| `--post` | Yes | WordPress post ID |

Output: JSON with `title`, `excerpt`, `location_query`, `topic`, `categories`, `tags`, `current_image_count`.

---

### `pictova plan`

Query image sources and display candidates. Does not download or process anything.

```bash
pictova plan --site <site> --post <post_id> [options]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--site` | Yes | — | Site profile name |
| `--post` | Yes | — | WordPress post ID |
| `--count` | No | profile default | Number of images to select |
| `--source` | No | `semantic` | Image source: `semantic`, `unsplash` |
| `--people-first` | No | false | Prefer images with human subjects |
| `--lang` | No | `tr` | Language hint for query construction |

Output: JSON list of candidate assets with `source`, `path_or_url`, `score`, `quality_score`, `flags`.

---

### `pictova process`

Run selection and processing (resize, format conversion) without publishing to WordPress.

```bash
pictova process --site <site> --post <post_id> [options]
```

Accepts the same flags as `plan`, plus:

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--engine` | No | `legacy` | Engine path: `legacy` or `native` |

Output: JSON with `selected_assets`, `rejected_assets`, `processed_paths`.

---

### `pictova attach`

Full pipeline: select → process → upload → place. Modifies WordPress.

```bash
pictova attach --site <site> --post <post_id> [options]
```

Accepts the same flags as `process`.

Output:
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

---

### `pictova serve`

Start the HTTP API server.

```bash
pictova serve [--host <host>] [--port <port>]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `8040` | Port |

See [HTTP API Reference](http-api.md) for endpoint documentation.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Validation error (missing flags, invalid post ID, etc.) |
| `2` | WordPress error (auth failure, post not found) |
| `3` | Source error (no candidates, API failure) |
| `4` | Processing error (quality gate blocked all candidates) |

All errors return structured JSON to stdout, not tracebacks.
