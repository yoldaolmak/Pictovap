# Configuration Reference

All configuration is via environment variables, loaded from `.env` in the repo root.
None of them are required — `pictovap demo` runs with zero configuration, and
`pictovap plan` runs against whichever sources/adapters you've actually configured.

## Image Source Adapters

| Variable | Required | Description |
|----------|----------|-------------|
| `PICTOVAP_LOCAL_IMAGE_DIR` | For the local source | Path to a directory of local image files |
| `UNSPLASH_ACCESS_KEY` | For the Unsplash source | Unsplash API access key |
| `DEPOSIT_API_KEY` | For the DepositPhotos source | DepositPhotos API key |
| `DEPOSIT_LOGIN_USER` | For the DepositPhotos source | DepositPhotos account username |
| `DEPOSIT_LOGIN_PASSWORD` | For the DepositPhotos source | DepositPhotos account password |

See [Image Source Adapters](../adapters/image-sources.md) for the full contract.

## CMS Adapters

| Variable | Required | Description |
|----------|----------|-------------|
| `WP_URL`, `WP_USER`, `WP_APP_PASSWORD` | For the WordPress adapter | WordPress site URL, username, and Application Password |
| `GHOST_URL`, `GHOST_ADMIN_API_KEY` | For the Ghost adapter | Ghost Admin API URL and key (`<id>:<secret>`) |
| `STRAPI_URL`, `STRAPI_API_TOKEN` | For the Strapi adapter | Strapi site URL and API token |

See [CMS Adapters](../adapters/cms-adapters.md) for the full contract.

## Vision-Backed Metadata (optional)

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | No | Enables Gemini Flash vision analysis for alt text/captions |

If neither `GEMINI_API_KEY` nor a local LM Studio instance (`localhost:1234`) is
available, `pictovap plan` falls back to the deterministic, dictionary-based
metadata generator — no vision key is required to run the pipeline.

## Example .env

```bash
# Image sources (all optional)
PICTOVAP_LOCAL_IMAGE_DIR=/path/to/images
UNSPLASH_ACCESS_KEY=abc123

# CMS adapter (optional; pick whichever you're publishing to)
WP_URL=https://example.com
WP_USER=myusername
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

# Vision-backed metadata (optional)
GEMINI_API_KEY=your-key-here
```
