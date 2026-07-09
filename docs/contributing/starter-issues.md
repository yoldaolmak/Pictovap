# Starter Issues

Looking to contribute to Pictovap? Here are several ideas for first pull requests, ranging from new adapters to core improvements.

## 1. Add Openverse Image Source Adapter
* **Problem**: We need a fully free, open-source image provider to supplement local files in the demo and production.
* **Expected Files**: `src/pictova/providers/openverse.py`, `tests/unit/test_openverse.py`
* **Acceptance Criteria**: Connects to Openverse API, searches by keyword, maps to standard candidate dict, respects license filtering.
* **Difficulty**: Medium
* **Credentials Required**: Yes (Free API key for testing)

## 2. Add Ghost CMS Placement Adapter
* **Problem**: Only WordPress is currently supported. Ghost is a popular alternative for independent publishers.
* **Expected Files**: `src/pictova/publishers/ghost.py`
* **Acceptance Criteria**: Can consume a `CMSPlacement` primitive and upload images via Ghost Admin API, returning success/failure.
* **Difficulty**: Medium
* **Credentials Required**: Yes (Local Ghost instance or test blog)

## 3. Add Strapi CMS Placement Adapter
* **Problem**: Headless CMS users need a placement adapter.
* **Expected Files**: `src/pictova/publishers/strapi.py`
* **Acceptance Criteria**: Uploads media via Strapi REST API and returns media IDs or URLs.
* **Difficulty**: Medium
* **Credentials Required**: Yes (Local Strapi instance)

## 4. Add Local Folder Image Metadata Loader
* **Problem**: The local source currently requires hardcoded dicts. It should read a directory of images and extract basic EXIF/IPTC metadata dynamically.
* **Expected Files**: `src/pictova/providers/local_folder.py`
* **Acceptance Criteria**: Reads a folder, parses basic metadata, yields candidate dicts.
* **Difficulty**: Easy
* **Credentials Required**: No

## 5. Improve Duplication Risk Scoring
* **Problem**: `FitScore` has a stub for `duplication_risk`, but it always returns 0.0.
* **Expected Files**: `src/pictova/engine/scoring.py` (or similar)
* **Acceptance Criteria**: Implements a check (e.g., against an SQLite history table or Bloom filter) to penalize images used recently.
* **Difficulty**: Medium
* **Credentials Required**: No

## 6. Add License Confidence Mapping
* **Problem**: License trust is hardcoded for a few specific strings.
* **Expected Files**: `src/pictova/core/license.py`
* **Acceptance Criteria**: Extract license logic into a dedicated module that parses standard SPDX identifiers or common strings and assigns confidence scores.
* **Difficulty**: Easy
* **Credentials Required**: No

## 7. Add Markdown Frontmatter Support
* **Problem**: `VisualBrief` parsing only looks at headings. It should read YAML frontmatter for tags/categories.
* **Expected Files**: `src/pictova/core/primitives.py`, `tests/unit/test_primitives.py`
* **Acceptance Criteria**: Uses `python-frontmatter` or regex to parse metadata at the top of an article and include it in the brief.
* **Difficulty**: Easy
* **Credentials Required**: No

## 8. Add Sample Publisher Profile
* **Problem**: We only have one demo profile.
* **Expected Files**: `examples/profiles/news-publisher.yaml`
* **Acceptance Criteria**: A realistic YAML configuration for a news or magazine site with strict image requirements.
* **Difficulty**: Easy
* **Credentials Required**: No

## 9. Add Sample Article Type
* **Problem**: The parser needs to be tested against diverse structures.
* **Expected Files**: `examples/articles/product-review.md`
* **Acceptance Criteria**: A realistic Markdown article representing a product roundup or review.
* **Difficulty**: Easy
* **Credentials Required**: No

## 10. Improve Alt Text Templates
* **Problem**: The fallback deterministic alt text generation is very basic.
* **Expected Files**: `src/pictova/engine/metadata.py`
* **Acceptance Criteria**: Better heuristics for generating alt text based on keywords and article context when AI generation is unavailable.
* **Difficulty**: Easy
* **Credentials Required**: No
