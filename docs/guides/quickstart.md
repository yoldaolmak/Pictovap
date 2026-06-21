# Quickstart

Get your first image attached to a WordPress post in 5 minutes.

## Prerequisites

- Python 3.9+
- A WordPress site with Application Passwords enabled
- An Unsplash developer account (free tier works)

## 1. Clone and install

```bash
git clone <repo-url> pictova
cd pictova
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## 2. Configure

```bash
cp .env.example .env
```

Open `.env` and fill in the minimum required fields:

```bash
# WordPress
WP_USER=your-wp-username
WP_PASSWORD=your-app-password        # Settings → Application Passwords

# Image source (at least one)
UNSPLASH_ACCESS_KEY=your-unsplash-key
```

## 3. Verify

```bash
pictova health
```

Expected output:
```json
{"status": "ok", "service": "pictova"}
```

## 4. Review a post

Pick any post ID from your WordPress site.

```bash
pictova review --site yoldaolmak --post 265713
```

This reads the post and shows what context Pictova derived. No images are touched.

## 5. Plan

```bash
pictova plan --site yoldaolmak --post 265713 --count 4
```

Shows the candidate images that would be selected. Still no changes to WordPress.

## 6. Attach

```bash
pictova attach --site yoldaolmak --post 265713 --count 4
```

Pictova selects, downloads, processes, uploads, and places 4 images into the post as Gutenberg image blocks.

---

## Next Steps

- [Installation](installation.md) — full setup including Mac Photos and local sources
- [CLI Reference](../reference/cli.md) — all flags and options
- [Site Profiles](../reference/profiles.md) — customizing behavior per site
