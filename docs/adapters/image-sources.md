# Image Source Adapters

Image source adapters supply candidate images to the Fit Score stage of the Pictovap pipeline.
Each adapter implements a common interface and returns a list of candidates with
the metadata needed for scoring.

## Interface Contract

An image source adapter must return candidates as a list of dicts with these fields:

```python
{
    "id": str,             # Unique identifier for this candidate
    "filename": str,       # Original filename
    "provider": str,       # Adapter name (e.g., "local", "unsplash")
    "source_type": str,    # "local", "api", or "url"
    "local_path": str,     # Absolute path if available, else None
    "source_url": str,     # Remote URL if applicable, else None
    "license": str,        # License identifier (e.g., "CC0", "unsplash", "editorial")
    "attribution": str,    # Required attribution string, or None
    "keywords": list[str], # Descriptive keywords
    "width": int,          # Pixel width
    "height": int,         # Pixel height
}
```

The Fit Score engine reads these fields and does not call the adapter directly.
This keeps scoring deterministic and adapter-independent.

## Existing Adapters

All five are classes implementing `search_candidates(query, count)` and are
verified against `ImageSourceAdapter` directly
(`issubclass(LocalFolderSource, ImageSourceAdapter)` and so on) in
`tests/unit/test_sources.py` and `tests/unit/test_adapter_contracts.py`.

### Local Files — `LocalFolderSource` (`src/pictova/providers/local.py`)

Reads images from a local directory. No credentials required.

```python
PICTOVAP_LOCAL_IMAGE_DIR=/path/to/images  # .env or environment variable
```

### Unsplash — `YOUnsplashDownloader` (`src/pictova/providers/unsplash.py`)

Queries the Unsplash API using keyword terms derived from the Visual Brief.

```python
UNSPLASH_ACCESS_KEY=your_key_here  # .env
```

### DepositPhotos — `DepositPhotosSource` (`src/pictova/providers/deposit.py`)

Queries licensed stock images. Requires an active account.

```python
DEPOSIT_API_KEY=your_key_here  # .env
```

### Openverse — `OpenverseSource` (`src/pictova/providers/openverse.py`)

Queries openverse.org, which aggregates openly licensed and public domain
media from many sources. No API key required — requests are restricted to
results licensed for commercial use and modification.

```python
# No .env variable needed. Add "openverse" to a profile's image_sources.
```

### Pexels — `PexelsSource` (`src/pictova/providers/pexels.py`)

Queries the Pexels API. Requires a free API key (sign up at
https://www.pexels.com/api/, approval is typically instant).

```python
PEXELS_API_KEY=your_key_here  # .env
```

## Writing a New Adapter

1. Create a new file in `src/pictova/providers/`, e.g. `pixabay.py`.
2. Implement a class with a `search_candidates(self, query: str, count: int) -> List[Dict]`
   method matching the contract above. The constructor must never raise or require
   credentials — a missing API key should only ever surface as an empty result once a
   search is actually attempted (see `ImageSourceAdapter` in `core/adapters.py`).
3. Add a dispatch branch for the adapter's source name in
   `core/sources.py::_fetch_from_source`, so it can be enabled per-publisher via
   `PublisherProfile.image_sources`.
4. Add a publisher profile example in `examples/profiles/` to demonstrate usage.
5. Write unit tests that mock the external API and assert the returned dict shape.

See the [Adapter Contribution Guide](../contributing/adapters.md) for step-by-step instructions.

## Credential Isolation

All credentials for external adapters must come from environment variables, never
from hardcoded values. The local demo must always be runnable without any `.env` file.
The mock adapter in `demo.py` demonstrates the correct credential-free pattern.
