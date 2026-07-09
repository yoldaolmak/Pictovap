# Pictovap Architecture

Pictovap is an open-source visual finishing engine for content publishers.
It is designed as a headless, modular pipeline that transforms raw text content
into a fully visually-populated publishing package.

## 1. Product Boundary

Pictovap solves the gap between "the text is written" and "the page is visually
complete and published in the CMS."

It is **not**:
- A stock photo search tool
- A Digital Asset Management (DAM) system
- A generic AI image generator

It is the article-aware automation layer that understands editorial layout needs,
selects matching images, tracks licensing provenance, generates metadata, and
places the images into the CMS.

## 2. Core Primitives

The architecture revolves around four core data primitives
(defined in `src/pictova/core/primitives.py`) that move sequentially
through the pipeline:

1. **[Visual Brief](concepts/visual-brief.md)**: Structured extraction of what
   imagery the article needs, based on heading structure and content.
2. **[Fit Score](concepts/fit-score.md)**: Transparent, deterministic evaluation
   of candidate images against the brief's requirements (context, quality, license).
3. **[Provenance Pack](concepts/provenance-pack.md)**: Persistent audit trail
   recording the origin, license, processing actions, and generated metadata
   for every selected image.
4. **[CMS Placement](concepts/cms-placement.md)**: CMS-agnostic plan for where
   images should be injected into the target platform.

## 3. Data Flow

The engine operates sequentially:

```text
Analysis (Visual Brief)
  -> Selection (Fit Score)
  -> Processing (Provenance Pack)
  -> Placement (CMS Placement)
```

Each stage produces a serializable object that feeds the next. The core engine
orchestrates this flow without any hardcoded dependencies on external systems.

## 4. Adapter Model

Pictovap connects to the outside world via two types of adapters:

- **Image Source Adapters** (`src/pictova/providers/`): Supply candidate images.
  Examples: Local directory, Unsplash, DepositPhotos.
- **CMS Placement Adapters** (`src/pictova/publishers/`): Consume the CMS
  Placement plan and execute native API calls.
  Examples: WordPress, Ghost, Strapi.

The core pipeline is adapter-agnostic.

## 5. Credential-Free Demo Path

The local demo (`make demo`) runs the entire pipeline end-to-end without
requiring any external credentials, API keys, or CMS connections. It uses:

- A local directory of mock image metadata as the source adapter.
- Deterministic rules for scoring and metadata generation.
- A mock CMS adapter that outputs the placement plan to a local JSON file.

## 6. WordPress as One CMS Adapter

While WordPress is currently the most production-hardened target, it is merely
one CMS adapter implementation. Pictovap does not assume WordPress as the
conceptual center. Any CMS with an API can be supported by writing a new adapter
that consumes the `CMSPlacement` primitive.

## 7. Yoldaolmak.com as Dogfooding Case Study

Pictovap was extracted from the production infrastructure of a travel publisher,
yoldaolmak.com. The site's profile (`src/pictova/profiles/yoldaolmak.py`) and
specific constraints represent a dogfooding case study and one possible
configuration, not the default path or product center.

## 8. Metadata Generation as Optional Adapter Behavior

While Pictovap produces standard metadata (Alt Text, SEO Title, Caption), the
exact mechanism is source-agnostic. It may be generated via an AI metadata
adapter (e.g., Gemini, Claude, LM Studio) or fall back to rule-based templates.
No specific AI model or "Vision Chain" is a required architectural component.

## 9. Legacy Package/CLI Compatibility

- **Product name:** Pictovap.
- Python package, directories (e.g., `src/pictova/`), and legacy CLI commands
  may remain `pictova` for backward compatibility.

## 10. Current Limitations

- Core logic was recently extracted from production; some internal dict passing
  is still being migrated to strict primitives.
- Only the WordPress CMS adapter is production-hardened; others are reference stubs.
- Publisher profiles exist as Python dataclasses but are not yet fully loadable
  from YAML in all pipeline paths.

## Engine Layout

```
src/
  pictova/
    app/          # CLI and REST API entrypoints
    core/         # Primitives and shared data structures
    engine/       # The pipeline (Analysis, Selection, Processing)
    filters/      # Image processing algorithms
    profiles/     # Publisher configurations
    providers/    # Image source adapters
    publishers/   # CMS integration adapters
```
