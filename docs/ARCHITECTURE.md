# Pictovap Architecture

Pictovap is designed as a headless, modular pipeline that transforms raw text content into a fully visually-populated publishing package. The architecture revolves around four core data primitives that move through the pipeline.

## The Pipeline

1. **Analysis Phase**: The engine analyzes the text, parsing headers (`H2`, `H3`), themes, and explicit directives to produce a `VisualBrief`.
2. **Selection Phase**: The pipeline queries configured image sources (e.g., local storage, Unsplash, DepositPhotos) using the `VisualBrief` parameters. It evaluates candidate images, generating a `FitScore` for each to ensure relevance and quality.
3. **Processing & Provenance Phase**: Selected images are downloaded, graded, resized, and converted to WebP. During this phase, metadata (alt text, captions) is generated via the Vision Chain (LLMs), and a `ProvenancePack` is constructed to ensure rights and history are tracked.
4. **Placement Phase**: Finally, the system creates a `CMSPlacement` plan. A CMS-specific adapter (like WordPress, Ghost, or Strapi) reads this plan and executes the native API calls to attach the assets to the target post.

## Core Primitives

The system's contracts are defined by these four models (found in `src/pictova/core/primitives.py`):

- **[Visual Brief](visual-brief.md)**: Extracted content requirements.
- **[Fit Score](fit-score.md)**: Transparent candidate evaluation.
- **[Provenance Pack](provenance-pack.md)**: Persistent asset record and metadata.
- **[CMS Placement](cms-placement.md)**: CMS-agnostic layout instructions.

## Engine Layout

```
src/
└── pictova/
    ├── app/          # CLI and REST API entrypoints
    ├── core/         # Primitives and shared data structures
    ├── engine/       # The pipeline (Selector, Processor, Quality, etc.)
    ├── filters/      # Image processing algorithms
    ├── profiles/     # Publisher configurations
    ├── providers/    # Image sources (Unsplash, Deposit, etc.)
    └── publishers/   # CMS integration adapters (WordPress, Ghost, etc.)
```
