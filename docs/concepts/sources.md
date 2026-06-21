# Image Sources

Pictova can draw images from multiple source types simultaneously or selectively. Each source has a driver, a configuration key, and a quality gate.

## Source Types

### Semantic / Visual Memory

The default source. Pictova queries an indexed local database of images — derived from Mac Photos, local directories, or any other indexed asset — using semantic matching against the post's content context.

```bash
pictova attach --site yoldaolmak --post 265713 --source semantic
```

Requires: `YO_VISUAL_MEMORY_DB` pointing to a populated index.  
See: [Visual Memory](visual-memory.md), [Semantic Selection](semantic-selection.md)

### Unsplash (Free)

Queries the Unsplash API for royalty-free images matching the post context.

```bash
pictova attach --site yoldaolmak --post 265713 --source unsplash
```

Requires: `UNSPLASH_ACCESS_KEY` in `.env`

### DepositPhotos (Licensed)

Queries DepositPhotos for licensed stock images. Selected images are downloaded, watermark-free, under the account's license tier.

Planned: **Pictova Depot** sub-layer.  
Requires: `DEPOSITPHOTOS_API_KEY`, active subscription.

### Local Directory

Any directory of image files (JPG, PNG, WebP) on disk can be used as a source. Pictova applies the same quality gate and semantic scoring to local files as to any other source.

Configuration: `LOCAL_IMAGE_DIR` in `.env` or via `--local-dir` flag (planned).

### Mac Photos Library

A specialized variant of semantic source. Your Mac Photos library is indexed by a separate visual memory runtime, enriched with Apple's on-device ML metadata (location, scene, faces, moment), and made available to Pictova through the visual memory database.

See: [Mac Photos Setup](../guides/mac-photos-setup.md)

## Source Selection Logic

When multiple sources are configured, Pictova:

1. Queries each enabled source in parallel
2. Scores all candidates using the semantic selection engine
3. Applies the quality gate (`quality.py`) to each batch
4. Merges and ranks across sources
5. Returns the top `--count` results

You can restrict to a single source with `--source <name>` or configure source priority in the site profile.

## Adding a New Source

Sources are implemented as provider modules under `src/pictova/providers/`. A new source needs:

1. A provider class that implements `query(context, count) -> list[Asset]`
2. Registration in `src/pictova/config.py`
3. A corresponding profile key in `src/pictova/profiles/`

See [Site Profiles](../reference/profiles.md) for configuration details.
