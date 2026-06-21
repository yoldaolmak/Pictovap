# HTTP API Reference

Start the server:

```bash
pictova serve --host 127.0.0.1 --port 8040
```

All request and response bodies are `application/json`.

---

## `GET /`

Service identification.

**Response:**
```json
{"service": "pictova", "status": "ok"}
```

---

## `GET /health`

Detailed health check.

**Response:**
```json
{"status": "ok", "service": "pictova"}
```

---

## `POST /review`

Read a post and return its derived context.

**Request:**
```json
{
  "site": "yoldaolmak",
  "post_id": 265713
}
```

**Response:**
```json
{
  "title": "Sinop Gezi Rehberi",
  "location_query": "Sinop",
  "topic": "travel guide",
  "categories": ["seyahat"],
  "tags": ["sinop", "karadeniz"],
  "current_image_count": 0
}
```

---

## `POST /plan`

Return candidate images without downloading or processing.

**Request:**
```json
{
  "site": "yoldaolmak",
  "post_id": 265713,
  "count": 4,
  "people_first": true,
  "source": "semantic"
}
```

**Response:**
```json
{
  "candidates": [
    {
      "source": "semantic",
      "path": "/path/to/sinop-harbor.jpg",
      "score": 0.91,
      "quality_score": 0.87,
      "city": "Sinop",
      "scene": "harbor"
    }
  ]
}
```

---

## `POST /process`

Select and process images without publishing.

**Request:** Same as `/plan`.

**Response:**
```json
{
  "selected_assets": [...],
  "rejected_assets": [...],
  "processed_paths": ["/tmp/pictova/sinop-harbor-processed.jpg"]
}
```

---

## `POST /attach`

Synchronous full pipeline. Blocks until complete.

**Request:**
```json
{
  "site": "yoldaolmak",
  "post_id": 265713,
  "count": 4,
  "people_first": true
}
```

**Response:**
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

For posts that take longer than a few seconds, use `POST /jobs/attach` instead.

---

## `POST /jobs/attach`

Async attach. Returns immediately with a job ID.

**Request:** Same as `/attach`.

**Response:**
```json
{
  "job_id": "abc123",
  "status": "pending",
  "created_at": "2026-06-21T10:00:00Z"
}
```

Poll with `GET /jobs/{job_id}`.

---

## `GET /jobs`

List all jobs.

**Response:**
```json
[
  {"job_id": "abc123", "status": "completed", "post_id": 265713},
  {"job_id": "def456", "status": "running", "post_id": 265800}
]
```

---

## `GET /jobs/{job_id}`

Get job status and result.

**Response (running):**
```json
{
  "job_id": "abc123",
  "status": "running",
  "created_at": "2026-06-21T10:00:00Z",
  "updated_at": "2026-06-21T10:00:05Z"
}
```

**Response (completed):**
```json
{
  "job_id": "abc123",
  "status": "completed",
  "created_at": "2026-06-21T10:00:00Z",
  "updated_at": "2026-06-21T10:00:09Z",
  "result": {
    "uploaded_media_ids": [101, 102, 103, 104],
    "inserted_blocks": [...],
    "duration_ms": 4210
  }
}
```

**Response (failed):**
```json
{
  "job_id": "abc123",
  "status": "failed",
  "error": "No candidates found for query: Sinop"
}
```

---

## Error Responses

All errors follow the same structure:

```json
{
  "error": "short_error_code",
  "message": "Human-readable description",
  "detail": {}
}
```

| HTTP Status | `error` | Cause |
|-------------|---------|-------|
| 400 | `validation_error` | Missing or invalid request fields |
| 401 | `auth_error` | WordPress credentials rejected |
| 404 | `post_not_found` | Post ID does not exist |
| 422 | `no_candidates` | No images passed quality gate |
| 500 | `internal_error` | Unexpected failure |
