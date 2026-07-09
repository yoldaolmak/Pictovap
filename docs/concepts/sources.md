# Image Sources

Pictovap can draw candidate images from multiple source types simultaneously or selectively.
Each source is an adapter that implements the standard candidate interface and returns
metadata-enriched candidates for the Fit Score stage.

## Source Types

### Local Directory

Reads image files from a local directory. No credentials required.

```
LOCAL_IMAGE_DIR=/path/to/images  # environment variable
```

This is the only source used by the local demo. No API key needed.

### Unsplash (Free API)

Queries the Unsplash API for royalty-free images matching the Visual Brief topic.

```
UNSPLASH_ACCESS_KEY=your_key_here  # .env
```

### DepositPhotos (Licensed Stock)

Queries DepositPhotos for licensed stock images.

```
DEPOSITPHOTOS_API_KEY=your_key_here  # .env
```

### Visual Memory DB (Local Semantic Index)

Queries a local SQLite database of indexed images. The database is built by a
separate indexer process and enriched with semantic metadata (location, scene,
activity, quality score).

```
YO_VISUAL_MEMORY_DB=/path/to/visual_memory.db  # .env
```

This source enables semantic matching against a personal or organizational image library.
It is optional; the demo and core pipeline do not require it.

## How Sources Are Combined

When multiple sources are configured in the publisher profile:

1. Each enabled source is queried independently.
2. All candidates are scored using the Fit Score engine.
3. Candidates are ranked across sources by final score.
4. Hard rejections (resolution, license) are applied before ranking.
5. The top candidates pass to the Provenance Pack stage.

You can restrict to a single source by configuring `image_sources` in the publisher profile.

## Adding a New Source

Sources are implemented as adapters under `src/pictova/providers/`. A new source needs:

1. A file in `src/pictova/providers/` implementing the candidate dict interface.
2. Registration in the profile system.
3. A credential key in `.env.example` (if credentials are needed).
4. Unit tests with mocked external calls.

See [Image Source Adapters](../adapters/image-sources.md) for the full interface contract
and [Writing Adapters](../contributing/adapters.md) for the contribution guide.

## Credential Isolation

All source credentials must come from environment variables. The local demo runs with
no `.env` file and no credentials. Sources that require credentials are simply not queried
when their environment variable is unset.

## Compatibility Note

Product name: Pictovap.
Python package and legacy CLI may remain `pictova` for backward compatibility.
