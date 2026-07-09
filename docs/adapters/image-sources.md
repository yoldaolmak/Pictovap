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

### Local Files (`src/pictova/providers/`)

Reads images from a local directory. No credentials required.

```python
LOCAL_IMAGE_DIR=/path/to/images  # .env or environment variable
```

### Unsplash (`src/pictova/providers/`)

Queries the Unsplash API using keyword terms derived from the Visual Brief.

```python
UNSPLASH_ACCESS_KEY=your_key_here  # .env
```

### DepositPhotos (`src/pictova/providers/`)

Queries licensed stock images. Requires an active account.

```python
DEPOSITPHOTOS_API_KEY=your_key_here  # .env
```

### Visual Memory DB (`src/pictova/providers/`)

Queries the local SQLite semantic index built from indexed image libraries.

```python
YO_VISUAL_MEMORY_DB=/path/to/visual_memory.db  # .env
```

## Writing a New Adapter

1. Create a new file in `src/pictova/providers/`, e.g. `openverse.py`.
2. Implement a function or class that accepts a `VisualBrief` (or its relevant fields)
   and returns a list of candidate dicts matching the contract above.
3. Register the adapter in `src/pictova/config.py` so it can be enabled via a profile.
4. Add a publisher profile key in `examples/profiles/` to demonstrate usage.
5. Write unit tests that mock the external API and assert the returned dict shape.

See the [Adapter Contribution Guide](../contributing/adapters.md) for step-by-step instructions.

## Credential Isolation

All credentials for external adapters must come from environment variables, never
from hardcoded values. The local demo must always be runnable without any `.env` file.
The mock adapter in `demo.py` demonstrates the correct credential-free pattern.
