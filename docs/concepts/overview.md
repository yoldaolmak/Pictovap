# Overview

## What Pictovap Is

Pictovap is an open-source visual finishing engine for content publishers.

Given an article, it analyzes the content structure, determines what imagery is needed,
evaluates candidate images, records provenance, and produces a CMS-agnostic placement plan.

Pictovap is not a stock photo search tool, a DAM, or a generic AI image generator.
It is the article-aware layer between written content and a visually complete,
publish-ready CMS page.

## The Four Primitives

Pictovap is built around four core data structures that move through the pipeline:

1. **[Visual Brief](visual-brief.md)** — A structured extraction of what imagery the article needs.
2. **[Fit Score](fit-score.md)** — A transparent, deterministic evaluation of each candidate image.
3. **[Provenance Pack](provenance-pack.md)** — An audit trail for every selected image.
4. **[CMS Placement](cms-placement.md)** — A CMS-agnostic plan for where images are placed.

## What Problem It Solves

Adding images to content is slow, repetitive, and requires domain judgment. An editor must:

1. Read the article to understand its visual needs
2. Search multiple sources for relevant images
3. Evaluate candidates against quality, license, and brand criteria
4. Process and rename files
5. Write alt text and captions
6. Place images at appropriate positions in the CMS

Pictovap automates this workflow. It reads article structure, derives a visual brief,
scores candidates from configured sources, selects the best matches, records provenance,
and produces placement instructions that a CMS adapter can execute.

## What It Is Not

Pictovap does not generate images. It selects, evaluates, and places images that already
exist — in a local directory, a licensed stock API, or any configured image source.

It does not replace editorial judgment for hero image selection or brand-defining visuals.
It automates the systematic work so editors can focus on decisions that matter.

## Adapter-Based Architecture

Pictovap connects to external systems via adapters:

- **Image Sources** — Local folders, Unsplash, DepositPhotos, Wikimedia, and others.
  See [Image Source Adapters](../adapters/image-sources.md).
- **CMS Targets** — WordPress, Ghost, Strapi, and others.
  See [CMS Adapters](../adapters/cms-adapters.md).

The core pipeline is independent of any specific adapter. The local demo runs with
no credentials, no CMS, and no external APIs.

## Compatibility Note

Product name: Pictovap.
The Python package is `pictovap` (since 0.3.0); `pictova` remains a deprecated alias.
Preferred public product name is Pictovap.
