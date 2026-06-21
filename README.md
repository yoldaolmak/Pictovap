# Pictova

**Visual Intelligence for Content**

Pictova finds, selects, processes, and places images into WordPress posts — from any source, without human intervention.

```bash
pictova attach --site yoldaolmak --post 265713 --count 4 --people-first
```

---

## What It Does

A travel post about Sinop should have photos of Sinop. Pictova reads the post, understands the context, queries every configured image source, selects the best matches, processes them to spec, and inserts native Gutenberg blocks. In under 60 seconds. Without an editor opening a browser.

**Sources it draws from:**

- Personal library — Mac Photos, indexed by location, scene, and activity
- Free APIs — Unsplash
- Licensed stock — DepositPhotos *(coming: Pictova Depot)*
- Local files — any directory of JPGs, PNGs, or WebPs on disk

**Where it delivers:**

- WordPress — media library upload + native Gutenberg image blocks + featured image
- Structured JSON — for custom downstream pipelines

---

## Part of the Meridyen Ecosystem

Pictova was born as the visual layer of **Meridyen**, the content platform behind [yoldaolmak.com](https://yoldaolmak.com). It is designed to be adopted by any content publisher — from solo bloggers to enterprise media teams.

```
Meridyen (platform)
├── YOOS-APP   — content generation engine
└── Pictova    — visual intelligence layer
    ├── Pictova Select   — semantic image selection
    ├── Pictova Depot    — licensed stock integration (planned)
    └── Pictova Memory   — visual memory index (Mac Photos + local)
```

See [Brand & Naming Doctrine](docs/architecture/naming.md) for the full story.

---

## Install

```bash
git clone <repo-url> pictova
cd pictova
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
cp .env.example .env  # fill in WP_USER, WP_PASSWORD, UNSPLASH_ACCESS_KEY
```

Verify:

```bash
pictova health
# {"status": "ok", "service": "pictova"}
```

Full setup: [Installation Guide](docs/guides/installation.md)

---

## Usage

### CLI

```bash
# Read post context (no changes)
pictova review --site yoldaolmak --post 265713

# Preview candidates (no changes)
pictova plan --site yoldaolmak --post 265713 --count 4 --people-first

# Process without publish
pictova process --site yoldaolmak --post 265713 --count 4 --people-first

# Full attach — selects, uploads, places
pictova attach --site yoldaolmak --post 265713 --count 4 --people-first

# Use native engine
pictova attach --site yoldaolmak --post 265713 --count 4 --engine native
```

### HTTP API

```bash
# Start server
pictova serve --host 127.0.0.1 --port 8040

# Async job (returns job_id immediately)
curl -s -X POST http://127.0.0.1:8040/jobs/attach \
  -H 'Content-Type: application/json' \
  -d '{"site":"yoldaolmak","post_id":265713,"count":4,"people_first":true}'

# Poll job status
curl -s http://127.0.0.1:8040/jobs/{job_id}
```

---

## Repository Structure

```
src/
  pictova/
    app/          CLI · HTTP API · job orchestration
    engine/       selector · processor · quality · metadata · publisher
    providers/    WordPress adapter
    profiles/     per-site configuration
  core/           legacy orchestration (being migrated)
  main.py         legacy entry point
ops/              maintenance scripts · indexers · repair tools
tests/
  unit/
  integration/
docs/
  concepts/       What and why
  guides/         How to set up and use
  reference/      CLI · HTTP API · config · profiles
  architecture/   How it is built
  ops/            Running in production
```

---

## Documentation

| | |
|--|--|
| [Overview](docs/concepts/overview.md) | What Pictova is and why it exists |
| [Quickstart](docs/guides/quickstart.md) | First attach in 5 minutes |
| [CLI Reference](docs/reference/cli.md) | All commands and flags |
| [HTTP API Reference](docs/reference/http-api.md) | All endpoints |
| [Configuration](docs/reference/configuration.md) | Environment variables |
| [Architecture](docs/architecture/overview.md) | System design |
| [Naming Doctrine](docs/architecture/naming.md) | Why Pictova, Meridyen ecosystem |
| [Runbook](docs/ops/runbook.md) | Day-to-day operations |

---

## Current Status

| Surface | Status |
|---------|--------|
| CLI (legacy engine) | Stable, production use |
| CLI (native engine) | Working, in active development |
| HTTP API | Working, no auth yet |
| Visual Memory (Mac Photos) | Stable, 284 indexed assets |
| Unsplash source | Stable |
| DepositPhotos source | Planned |
| Persisted job store | Planned |
| Structured logging | Planned |

Tests: `python3 -m pytest -q` → 19 passed

---

## License

MIT
