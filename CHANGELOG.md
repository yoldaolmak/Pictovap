# Changelog

## [Unreleased]

## [0.2.0] — 2026-07-09

### Added
- First public Open Source release.
- Local credential-free demo (`make demo`) demonstrating the core primitives.
- Extensive OSS documentation in `docs/` covering architecture, concepts, and adapter model.
- Standardized primitives: `VisualBrief`, `FitScore`, `ProvenancePack`, `CMSPlacement`.
- Sample publisher profiles and articles.
- OSS hygiene files (SECURITY.md, CODE_OF_CONDUCT.md, CONTRIBUTING.md).

### Changed
- Renamed package from `vil` → `pictova` across all modules, CLI, and pyproject.toml
- Removed AI agent coordination files (`AI_COORDINATION.md`, `QWEN_STATUS.md`)
- Full documentation restructure: concepts / guides / reference / architecture / ops

### Added
- Brand doctrine document: `docs/architecture/naming.md`
- CLI reference: `docs/reference/cli.md`
- HTTP API reference: `docs/reference/http-api.md`
- Configuration reference: `docs/reference/configuration.md`
- Site profiles reference: `docs/reference/profiles.md`
- Concept docs: overview, visual memory, semantic selection, pipeline, sources
- Guides: quickstart, installation, Mac Photos setup, WordPress setup, adding sources
- Architecture docs: system overview, native vs legacy, engine modules
- Ops docs: runbook, indexing, monitoring

## [0.1.0] — 2026-06

### Added
- `src/pictova/` canonical package root (formerly `src/vil/`)
- CLI: `pictova attach`, `pictova plan`, `pictova process`, `pictova review`, `pictova health`, `pictova serve`
- HTTP API: `/health`, `/review`, `/plan`, `/process`, `/attach`, `/jobs/attach`, `/jobs`, `/jobs/{id}`
- Async job registry (`src/pictova/app/state.py`)
- Native engine path (`src/pictova/engine/`): selector, processor, quality, metadata, publisher, gallery
- Vision-backed metadata with fallback to deterministic mode
- Mac Photos semantic index integration via `YO_VISUAL_MEMORY_DB`
- Apple Photos ML enrichment (location, scene, faces, blur/exposure)
- Structured attach output contract with `selected_assets`, `rejected_assets`, `uploaded_media_ids`, `inserted_blocks`, `duration_ms`
- `pyproject.toml` console script: `pictova`
- 19 passing tests
