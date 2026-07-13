# Adapter Architecture Overview

Pictovap uses an adapter-based architecture to remain CMS-agnostic and source-agnostic.
The core pipeline — Visual Brief → Fit Score → Provenance Pack → CMS Placement —
is independent of any specific image provider or content management system.

Adapters are the boundary between the core engine and the external world.

## Adapter Types

### Image Source Adapters

Image source adapters supply candidate images to the Fit Score stage.
They implement a standard interface and return a list of candidates with
metadata (dimensions, license, keywords, source URL).

Current adapters:
- **Local** — reads image files from a configured directory (production-ready)
- **Unsplash** — queries the Unsplash API (requires `UNSPLASH_ACCESS_KEY`)
- **DepositPhotos** — queries licensed stock (requires `DEPOSIT_API_KEY`)
- **Openverse** — queries openly licensed/CC media (no key required)
- **Pexels** — queries the Pexels API (requires `PEXELS_API_KEY`)

The demo uses mock candidates that do not call any adapter.

See: [Image Source Adapters](image-sources.md)

### CMS Adapters

CMS adapters consume the `CMSPlacement` plan and execute the native API calls
to place images in the target CMS.

Current adapters:
- **WordPress/Gutenberg** — production-tested; uploads to media library, inserts blocks
- **Ghost** — stub/reference implementation
- **Strapi** — stub/reference implementation
- **Mock** — writes output to JSON only; used by the demo

See: [CMS Adapters](cms-adapters.md)

## Where Adapters Live

```
src/
└── pictovap/
    ├── providers/    # Image source adapters
    └── publishers/   # CMS placement adapters
```

Third-party adapters can live in independent distributions and register their
adapter class through the `pictovap.image_sources` or `pictovap.cms` Python
entry-point group. Pictovap discovers installed plugins without importing them
until they are requested.

## The Core Engine Is Adapter-Free

The four primitives (`VisualBrief`, `FitScore`, `ProvenancePack`, `CMSPlacement`)
and the demo pipeline (`src/pictovap/demo.py`) have no dependencies on any specific
adapter. They can be tested and run in complete isolation.

## Adding a New Adapter

See the contribution guides:

- [Writing Image Source Adapters](image-sources.md)
- [Writing CMS Adapters](cms-adapters.md)
- [Contribution Guide for Adapters](../contributing/adapters.md)
- [Building Third-Party Adapter Plugins](../contributing/plugins.md)
