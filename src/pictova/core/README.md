# Pictovap Core

Core modules of the Pictovap visual finishing engine: primitives, language
detection, image processing/filtering, and metadata generation.

## Modules

### Primitives
- `primitives.py`: Visual Brief, Fit Score, Provenance Pack, CMS Placement — the
  four core data structures the rest of the pipeline is built around.
- `profile.py`: Publisher Profile loading (site name, CMS type, language,
  output/filename/alt-text/caption rules, source adapters).

### Language
- `language.py`: Deterministic local word-marker language detection (used by
  the credential-free demo path). Currently recognizes English and Turkish.

### Image processing
- `processor.py`: Image load, crop, filter, resize, WebP export pipeline.
- `filter.py`: Adaptive cinematic color-grading filter.

### Metadata
- `demo_metadata.py`: Deterministic, localized alt-text/caption generation used
  by the credential-free demo (no API calls, dictionary-based). Not to be
  confused with `metadata_generator.py` (LLM-backed) or `engine/metadata.py`
  (native engine, also LLM-backed) — see `docs/architecture/native-vs-legacy.md`.
- `metadata_generator.py`: LLM-backed metadata generation (alt/title/caption/
  description/keywords) with DB caching, used by the vision-chain-driven path.
- `media_publish.py`: Slug/filename generation, scene-token normalization, and
  publish-path utilities.
- `media_quality.py`: Metadata/asset validation and quality checks.

### Data
- `database.py`: Visual Memory (SQLite) component — indexing and lookups for
  previously processed assets.
- `selection.py`: Candidate scoring/selection helpers.
