# Configuration Reference

All configuration is via environment variables, loaded from `.env` in the repo root.

## WordPress

| Variable | Required | Description |
|----------|----------|-------------|
| `WP_USER` | Yes | WordPress username |
| `WP_PASSWORD` | Yes | WordPress Application Password |

## Image Sources

| Variable | Required | Description |
|----------|----------|-------------|
| `UNSPLASH_ACCESS_KEY` | For Unsplash source | Unsplash API access key |
| `DEPOSITPHOTOS_API_KEY` | For Deposit source | DepositPhotos API key |
| `LOCAL_IMAGE_DIR` | For local source | Path to local image directory |
| `YO_VISUAL_MEMORY_DB` | For semantic source | Path to visual memory SQLite database |

## AI / Vision

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | No | Enables vision-backed metadata generation (Claude) |
| `OPENAI_API_KEY` | No | Alternative vision provider |

Without a vision key, Pictova falls back to deterministic metadata (filename, index fields). Vision keys improve alt text and caption quality.

## Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | SQLite in repo | Override database connection (PostgreSQL for production) |

## HTTP Server

| Variable | Default | Description |
|----------|---------|-------------|
| `PICTOVA_HOST` | `127.0.0.1` | Default bind address for `pictova serve` |
| `PICTOVA_PORT` | `8040` | Default port |

## Defaults

| Variable | Default | Description |
|----------|---------|-------------|
| `PICTOVA_DEFAULT_COUNT` | `4` | Images per post when `--count` is omitted |
| `PICTOVA_DEFAULT_ENGINE` | `legacy` | Engine path: `legacy` or `native` |

## Example .env

```bash
# WordPress
WP_USER=myusername
WP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

# Image sources
UNSPLASH_ACCESS_KEY=abc123
YO_VISUAL_MEMORY_DB=/Users/yoldaolmak/Projects/Pictova/data/visual_memory.db

# Vision (optional, improves metadata quality)
ANTHROPIC_API_KEY=sk-ant-...

# Server
PICTOVA_PORT=8040
```
