# Good First Issues

This page lists well-scoped contribution opportunities for new contributors to Pictovap.
Each item links to the relevant code and documentation so you can get started immediately.

## Image Source Adapters

These adapters supply candidate images to the pipeline. Each follows the same interface
contract described in [Image Source Adapters](../adapters/image-sources.md).

### Openverse Adapter
- **Scope:** New file in `src/pictova/providers/openverse.py`
- **API:** https://api.openverse.org/ (no key required for basic use)
- **What it does:** Queries Openverse for CC-licensed images matching the Visual Brief topic
- **Good for:** First adapter contribution; the API is open and simple

### Pexels Adapter
- **Scope:** New file in `src/pictova/providers/pexels.py`
- **API:** https://www.pexels.com/api/ (free key)
- **What it does:** Queries Pexels for royalty-free images
- **Good for:** Adapter contributors familiar with REST APIs

### Pixabay Adapter
- **Scope:** New file in `src/pictova/providers/pixabay.py`
- **API:** https://pixabay.com/api/docs/ (free key)
- **What it does:** Queries Pixabay for CC0 images
- **Good for:** Similar to Pexels; straightforward REST pattern

### Wikimedia Commons Adapter
- **Scope:** New file in `src/pictova/providers/wikimedia.py`
- **API:** https://commons.wikimedia.org/wiki/API:Main_page (no key)
- **What it does:** Searches freely licensed media for editorial and factual content
- **Good for:** Contributors interested in open knowledge and licensing

---

## CMS Adapters

These adapters read the `CMSPlacement` plan and place images in a target CMS.
The interface is described in [CMS Adapters](../adapters/cms-adapters.md).

### Ghost Adapter (Complete the Stub)
- **Scope:** Expand `src/pictova/publishers/ghost_publisher.py` from stub to working
- **API:** https://ghost.org/docs/admin-api/ (local Ghost instance for testing)
- **What it does:** Uploads images and attaches them to Ghost posts via Admin API
- **Good for:** Contributors with a Ghost instance available for testing

### Hugo Static Site Adapter
- **Scope:** New file in `src/pictova/publishers/hugo_adapter.py`
- **What it does:** Writes images to the Hugo `static/` directory and generates shortcodes
- **Good for:** Static site enthusiasts; no external API required

---

## Publisher Profiles

### Example Profile: News Publisher
- **Scope:** New file `examples/profiles/news-publisher.yaml`
- **What it does:** Demonstrates a newspaper-style profile with different forbidden patterns,
  shorter captions, and editorial-only license requirements
- **Good for:** First contribution with zero code changes

### Example Profile: E-commerce Publisher
- **Scope:** New file `examples/profiles/ecommerce-publisher.yaml`
- **What it does:** Profile with product-first image preferences
- **Good for:** YAML-only contribution

---

## Documentation

### Translate the Quickstart
- **Scope:** New file `docs/quickstart.<lang>.md`
- **What it does:** Translates the quickstart guide to another language
- **Good for:** Non-English speakers who want to contribute documentation

### Write a Tutorial
- **Scope:** New file under `docs/guides/`
- **What it does:** Step-by-step guide for a specific use case
- **Good for:** Contributors who have used Pictovap and want to share their workflow

---

## How to Claim an Issue

Open a GitHub issue saying you want to work on one of these items. Include:
1. Which item you're claiming
2. Your intended approach
3. Any questions

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for the full pull request process.
