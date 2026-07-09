# Visual Memory DB

Visual Memory DB is an optional local image index that powers semantic candidate
selection from a personal or organizational image library. It is a SQLite database
enriched with metadata from indexed image sources.

This is an optional, advanced feature. The local demo and core pipeline run
without it.

## What It Contains

Each record in the index represents one image:

| Field | Description |
|---|---|
| `source_path` | Absolute path to the original file |
| `filename` | File name |
| `title` | Human-readable title |
| `description` | Generated or source description |
| `summary` | Short text summary |
| `location` | Place name where the photo was taken |
| `city` | City extracted from metadata |
| `country` | Country |
| `activity` | Activity detected (hiking, dining, etc.) |
| `scene` | Scene type (landscape, street, interior, etc.) |
| `quality_score` | Composite score: sharpness, exposure, composition |
| `face_count` | Number of faces detected |
| `blur_score` | Blur indicator |

## When to Use It

Use Visual Memory DB when you have a large personal or organizational image library
that you want to query semantically — matching images to article topics and locations
without manual tagging.

It is particularly useful when:
- You have hundreds or thousands of images with rich metadata
- You need location-aware selection (e.g., "photos from Istanbul")
- You want to prefer owned photography over stock APIs

## Configuration

```
YO_VISUAL_MEMORY_DB=/path/to/visual_memory.db
```

Set this environment variable to point to a populated index. When unset, this source
is silently skipped — the pipeline continues with other configured sources.

## Building the Index

The index is built by a separate indexer process that scans image directories or
library exports and writes to `visual_memory.db`. The consumer runtime (Pictovap)
reads the index but never writes to it.

Indexer implementation details are outside the scope of this document. Contributions
to document or generalize the indexer are welcome.

## Compatibility Note

Product name: Pictovap.
Python package and legacy CLI may remain `pictova` for backward compatibility.
The Visual Memory indexer was originally developed for the yoldaolmak.com Mac Photos
library. The consumer interface is generalized and works with any populated index.
