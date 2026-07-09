# Engine Modules

All modules live in `src/pictova/engine/`. Each has a single responsibility.

## `attach.py` — Pipeline Orchestrator

The entry point for the engine layer. Ties all other modules together.

Key functions:
- `build_attach_plan(payload)` — selection phase
- `build_process_result(payload)` — processing phase
- `execute_native_attach(payload)` — full pipeline

Called by `src/pictova/app/jobs.py`. Does not call app-layer code.

## `selector.py` — Candidate Selection

Queries configured image sources and returns ranked candidates.

Key functions:
- `resolve_source_images(context, count, source)` — query a specific source
- Internal scoring logic across semantic fields

Inputs: post context dict, requested count, source name.  
Output: list of `Asset` objects with scores.

## `processor.py` — Image Processing

Downloads and prepares selected images for upload.

Key functions:
- `process_selected_images(assets, profile)` — download, resize, convert

Inputs: selected `Asset` list, site profile.  
Output: list of processed file paths with dimensions.

## `quality.py` — Quality Gate

Filters out images that do not meet standards.

Key functions:
- `validate_native_metadata(metadata)` — per-image check
- `quality_gate_native_batch(assets)` — batch gate, returns (passed, rejected)

Thresholds are profile-configurable. Rejected assets are surfaced in the output contract's `rejected_assets` field.

## `metadata.py` — Metadata Generation

Produces alt text, captions, and titles for processed images.

Key functions:
- `build_basic_metadata_map(assets, context)` — deterministic, no API
- `build_native_metadata_map(assets, context)` — vision-backed when key present

The native metadata function calls external model providers for vision analysis when an API key is configured. Falls back to basic metadata per-image if the vision call fails.

## `publisher.py` — WordPress Publisher

Uploads processed images to WordPress and inserts Gutenberg blocks.

Key functions:
- `publish_processed_images(processed, metadata, profile)` — upload + insert

Inputs: processed file list, metadata map, site profile.  
Output: `uploaded_media_ids`, `inserted_blocks`.

## `gallery.py` — Block Builder

Constructs native WordPress Gutenberg block markup for single images and galleries.

Used by `publisher.py`. No external I/O.
