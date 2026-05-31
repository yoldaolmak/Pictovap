# Visual Memory Core

This package builds the core visual memory system for a content generation workflow.

Scope:

- scan Apple Photos originals
- scan an external HDD archive
- extract file metadata, folder context, and available EXIF-like fields
- enrich every image with AI-style searchable descriptors
- store everything in one structured SQLite database

Out of scope:

- Google Drive
- export derivatives
- UI

## Architecture

- `visual_memory.sources`: visible-file discovery from Apple Photos and external disks
- `visual_memory.analyzer`: metadata and EXIF-like extraction
- `visual_memory.enrich`: AI-style enrichment for `scene`, `location`, `activity`, `objects`, `story_tags`, `keywords`
- `visual_memory.db`: single SQLite asset index plus FTS search
- `visual_memory.indexer`: end-to-end scan and indexing pipeline
- `visual_memory.article`: article heading and section parsing
- `visual_memory.planner`: slot planning layer that can consume the index
- `visual_memory.service`: embeddable API surface
- `visual_memory.stock`: stock fallback provider clients
 - `visual_memory.seo`: SEO metadata helpers

## Indexed Data

Each asset stores:

- source type
- full path
- folder path
- filename and extension
- checksum
- dimensions
- capture date
- camera / lens / focal / f-number / exposure / ISO when available
- place metadata
- album and keyword metadata
- raw metadata snapshots
- AI-style enrichment:
  - `summary`
  - `scene`
  - `location`
  - `activity`
  - `objects`
  - `story_tags`
  - `keywords`
  - `quality_score`
  - `orientation`
  - `capture_context`

## Source Rules

- Apple Photos is treated as read-only source data.
- Apple Photos can be used for indexing from locally visible originals and available metadata.
- If a later workflow needs final full-quality processing, the iCloud original must be downloaded first.
- Hidden files and hidden folders are skipped during scanning.

## Example

```python
from pathlib import Path

from visual_memory import VisualMemoryComponent, VisualMemoryConfig

component = VisualMemoryComponent(
    VisualMemoryConfig(
        database_path=Path("~/Library/Application Support/photo_ai/visual_memory.db").expanduser(),
        external_roots=[Path("/Volumes/TravelArchive")],
    )
)

indexed = component.rebuild_index()
print(indexed)

rows = component.search_assets("roma kolezyum ayse kemal", limit=10)
for row in rows:
    print(row["source_path"], row["scene"], row["activity"], row["quality_score"])
```

## Slot Planning

The planner layer remains available on top of the core index:

- parse article sections
- map sections to visual slots
- propose candidate images per heading

This uses the core database; it does not require any export system.

## Depositphotos Fallback

For missing slots, the component can query Depositphotos as a stock fallback provider.

Configuration:

```python
from pathlib import Path

from visual_memory import VisualMemoryComponent, VisualMemoryConfig

component = VisualMemoryComponent(
    VisualMemoryConfig(
        database_path=Path("~/Library/Application Support/photo_ai/visual_memory.db").expanduser(),
        depositphotos_search_url="https://partner-api.example.com/search",
        depositphotos_api_key="YOUR_KEY",
        depositphotos_api_secret="YOUR_SECRET",
        depositphotos_affiliate_id="YOUR_AFFILIATE_ID",
    )
)

results = component.search_depositphotos("rome trastevere restaurant ivy", limit=5)
for item in results:
    print(item.asset_id, item.title, item.preview_url, item.landing_url)
```


Notes:
- This layer is intended for search and fallback selection.
- Depositphotos Partner API access requires approved credentials and endpoint details.

Credentials are stored in `depositphotos_credentials.json` at the repo root. The component now reads that file automatically, so updating the JSON is all that is needed when the key/secret change (or pass `deposit_config_path=Path(...)` to `VisualMemoryComponent` if you keep the file elsewhere). Then `component.search_depositphotos(...)` works without manual wiring.

Reference sources used for this integration design:

- https://depositphotos.com/api-program/signup.html
- https://depositphotos.com/api-agreement.html
## SEO Metadata

Every asset exported via the workflow can be annotated before it reaches WordPress. Call `seo_fields_for(slot_label, target_text)` to get alt/title/caption/description/keywords/credit strings that stay short and descriptive, and run `embed_image_metadata(path, seo_fields)` with `exiftool` (it's tolerant if the tool is missing). These embedded IPTC/XMP fields populate the WordPress `alt`, `title`, `caption`, and `description` fields, while `ImageObject` JSON-LD can reuse the same values so Google sees consistent attribution.

Text conventions:
- sentences never end with a full stop
- `alt` and `title` stay concise and focus on the landmark
- `caption` echoes the short description
- `description` ends with `kaynak: 📷 Depositphotos` so the source is visible only there
- keywords remain limited to 4–6 tokens tied to the location/topic

Call `annotate_exported_image(path, slot_label, target_description)` from `visual_memory.stock` whenever you finalize a downloaded asset so the metadata rule set is applied automatically.
