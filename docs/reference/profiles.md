# Site Profiles

A site profile bundles per-site configuration: WordPress URL, default behavior, source priorities, and block placement rules.

## Location

Profiles live in `src/pictova/profiles/`. The active profile is selected via `--site <name>`.

```
src/pictova/profiles/
  __init__.py
  yoldaolmak.py     ← yoldaolmak.com profile
  mysite.py         ← add yours here
```

## Profile Schema

```python
# src/pictova/profiles/mysite.py

SITE_URL = "https://mysite.com"
WP_PATH = "/home/myuser/public_html"   # for wp-cli on server

# Selection defaults
DEFAULT_COUNT = 4
PEOPLE_FIRST = False
SOURCE_PRIORITY = ["semantic", "unsplash"]
MIN_QUALITY_SCORE = 0.6

# Processing
TARGET_WIDTH = 1200
TARGET_HEIGHT = 800
OUTPUT_FORMAT = "webp"

# WordPress placement
BLOCK_TYPE = "image"           # "image" or "gallery"
SET_FEATURED_IMAGE = True
INSERT_POSITION = "after_intro"   # "after_intro", "distributed", "end"
```

## The yoldaolmak Profile

The active profile for yoldaolmak.com is optimized for Turkish travel content:

- Source priority: Visual Memory first (personal library), Unsplash fallback
- People first: enabled (travel content benefits from human subjects)
- Insert position: distributed through post body
- Featured image: enabled
- Output format: WebP with JPEG fallback

## Insert Positions

| Value | Behavior |
|-------|----------|
| `after_intro` | Place all images after the first H2 |
| `distributed` | Distribute images evenly through H2 sections |
| `end` | Place all images at the end of the post |
| `manual` | Return processed images without inserting (for custom pipelines) |

## Using a Profile

```bash
# CLI
pictova attach --site mysite --post 265713

# HTTP
curl -X POST http://127.0.0.1:8040/attach \
  -d '{"site":"mysite","post_id":265713}'
```

## Creating a Profile

1. Copy `src/pictova/profiles/yoldaolmak.py` to `src/pictova/profiles/mysite.py`
2. Update `SITE_URL`, `WP_PATH`, and any behavioral defaults
3. Use `--site mysite` in commands
