# Overview

## What Pictova Is

Pictova is a visual intelligence layer for content publishing. Given a WordPress post, it finds the right images, processes them, and places them — without human intervention.

It connects to any combination of image sources:

- **Free APIs**: Unsplash and similar open providers
- **Licensed stock**: DepositPhotos and compatible APIs
- **Personal library**: Mac Photos via indexed visual memory
- **Local files**: Any directory of JPGs, PNGs, or WebPs on disk

It delivers to any combination of destinations:

- **WordPress**: native Gutenberg blocks, media library upload, featured image
- **Local output**: processed files with generated metadata
- **Structured JSON**: for custom downstream pipelines

## What Problem It Solves

Adding images to content is slow, repetitive, and cognitively expensive. A human editor must:

1. Read the post to understand its context
2. Search multiple sources for relevant images
3. Download, resize, and rename files
4. Upload to WordPress
5. Write alt text and captions
6. Place images at appropriate positions
7. Repeat for every post

Pictova automates all seven steps. It reads the post context, derives a semantic query, scores candidates from every configured source, selects the best matches, processes them to spec, generates metadata, and inserts native WordPress blocks.

A post that takes 20 minutes of manual work takes under 60 seconds with Pictova.

## What It Is Not

Pictova does not generate images. It selects, processes, and places images that already exist — in your library, on your disk, or via licensed providers.

It does not replace editorial judgment for hero image selection or brand-defining visuals. It automates the volume work so editors can focus on the decisions that matter.

## Where It Lives

Pictova was born as the visual layer of **Meridyen**, the content platform behind [yoldaolmak.com](https://yoldaolmak.com). It is designed to operate as a standalone application that any content publisher can adopt — from solo travel bloggers to enterprise media teams.

See [Brand & Naming Doctrine](../architecture/naming.md) for the full Meridyen ecosystem map.

## Two Ways to Run It

**CLI** — for single posts and operator workflows:
```bash
pictova attach --site yoldaolmak --post 265713 --count 4 --people-first
```

**HTTP** — for automation, batch pipelines, and integrations:
```bash
pictova serve --host 127.0.0.1 --port 8040
curl -X POST http://127.0.0.1:8040/jobs/attach \
  -H 'Content-Type: application/json' \
  -d '{"site":"yoldaolmak","post_id":265713,"count":4,"people_first":true}'
```

See [CLI Reference](../reference/cli.md) and [HTTP API Reference](../reference/http-api.md) for full details.
