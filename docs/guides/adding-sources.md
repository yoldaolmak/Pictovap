# Adding Image Sources

## Currently Supported Sources

| Source | Key | Status | Requires |
|--------|-----|--------|----------|
| Visual Memory (Mac Photos / local index) | `semantic` | Stable | `YO_VISUAL_MEMORY_DB` |
| Unsplash | `unsplash` | Stable | `UNSPLASH_ACCESS_KEY` |
| DepositPhotos | `deposit` | Planned | `DEPOSITPHOTOS_API_KEY` |
| Local directory | `local` | Planned | `LOCAL_IMAGE_DIR` |

## Configuring Unsplash

1. Create a free account at [unsplash.com/developers](https://unsplash.com/developers)
2. Create a new application
3. Copy the **Access Key**

In `.env`:
```bash
UNSPLASH_ACCESS_KEY=your-access-key
```

Unsplash free tier: 50 requests/hour. For production volume, apply for production access.

## Configuring Visual Memory

See [Mac Photos Setup](mac-photos-setup.md) for the full indexing guide.

Quick `.env` entry:
```bash
YO_VISUAL_MEMORY_DB=/path/to/visual_memory.db
```

## Source Priority

The order in which sources are queried is controlled by the site profile:

```python
# src/pictova/profiles/yoldaolmak.py
source_priority = ["semantic", "unsplash"]
```

Sources are queried in order. If the first source returns enough high-quality candidates, subsequent sources are skipped. If not, the next source is queried and results merged.

## Implementing a Custom Source

Implement the provider interface:

```python
# src/pictova/providers/mysource.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Asset:
    source_path: str
    source: str
    score: float
    metadata: dict

def query(context: dict, count: int) -> list[Asset]:
    """
    context: {location, topic, activity, people_first, ...}
    count: requested number of candidates (return more for quality gate headroom)
    """
    ...
```

Register in `src/pictova/config.py`:

```python
SOURCE_DRIVERS = {
    "semantic": "src.pictova.providers.visual_memory",
    "unsplash": "src.pictova.providers.unsplash",
    "mysource": "src.pictova.providers.mysource",   # add here
}
```

Add to your site profile's `source_priority` list.
