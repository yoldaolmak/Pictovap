# Changelog

## [Unreleased]

### Added

* Adoption telemetry now records direct 90-day GitHub issue/PR and issue-comment
  totals beside the PyPI and repository snapshots.
* Vision requests now cap inline image dimensions and unbounded article context
  before sending data to a model, reducing avoidable token usage.

## [0.7.7] - 2026-07-22

### Added

* Vision templates now expose bounded output-token budgets so live metadata
  calls do not reserve a larger completion than the selected template needs.
* `make contribution-check` provides a fast contributor gate without Node/npm.
* `make install` now reports the supported Python floor before invoking pip.

### Fixed

* Standalone adapter scaffolds no longer trigger pytest collection warnings for
  adapter names beginning with `test`.
* Single-file documentation and security checks no longer fail on the global
  coverage threshold when run independently.
* Criticality collection now grants the pinned OpenSSF tool read-only issue and
  pull-request access so activity signals are not silently omitted.

## [0.7.6] - 2026-07-22

### Added
* A pinned OpenSSF Criticality Score workflow with checksum and JSON artifact
  validation.
* Runnable Pixabay and Wikimedia standalone provider references with mocked
  response mapping and public contract tests.
* CI coverage for standalone adapter installation, discovery, conformance, and
  wheel builds.
* Publisher Profile v1: versioned YAML, strict validation, and a bundled JSON schema
* stable `pictovap.api` public API module and built-in Markdown/HTML report renderers
* report-renderer plugin discovery and reusable renderer contract assertions
* API Stability Policy defining stable, experimental, and internal integration surfaces
* `pictovap adapter check` for safe, machine-readable installed-plugin conformance reports
* complete independently installable external HTML renderer package example and Framework Guide

### Changed
* Adapter scaffolds now pass a default flake8 run without contributors needing
  to edit generated boilerplate first.
* Contributor documentation now states the Python 3.10+ requirement and keeps
  credential-free setup separate from optional live integrations.
* public development guidance is now model-neutral and stale project handoff files were removed
* adapter status language now distinguishes mocked API coverage from live deployment validation
* semantic metadata validation uses provider-neutral source categories

### Fixed
* Adoption and framework walkthroughs no longer point at source-checkout-only
  article paths.
* Gutenberg H2 and H3 headings now preserve readable text across inline bold,
  italic, and link markup without leaking HTML into placement targets

## [0.7.5] - 2026-07-19

### Fixed
* WordPress post planning now reports safe, actionable authentication,
  permission, missing-post, timeout, and connection errors without exposing
  credentials, response bodies, or private post content

## [0.7.4] - 2026-07-19

### Changed
* discovery language now frames Pictovap as publisher infrastructure for the
  universal image-search and in-article placement problem; WordPress Gutenberg
  remains the first-class integration rather than the product boundary

## [0.7.3] - 2026-07-19

### Changed
* public discovery metadata now speaks in the language of the WordPress
  publisher pain: finding free images and adding them to Gutenberg articles
  rather than describing Pictovap's internal solution components

## [0.7.2] - 2026-07-19

### Changed
* public metadata and documentation now lead with the WordPress publisher pain:
  finding rights-aware free-stock images, placing them under Gutenberg content,
  and retaining provenance through publishing
* PyPI keywords and GitHub topics now prioritize WordPress, Gutenberg, CMS
  publishing, image search, free-stock images, image placement, and media-library work

## [0.7.1] - 2026-07-18

### Added
* e-commerce and news publisher profile examples
* a no-network CLI regression test for WordPress post planning dispatch

### Changed
* GitHub and PyPI metadata now position Pictovap around WordPress Gutenberg
  and Markdown inputs, rights-aware visual plans, and CMS placement
* repository topics now prioritize publisher, Gutenberg, CMS, provenance, and
  accessibility discovery over generic computer-vision and LLM terms

## [0.7.0] - 2026-07-17

### Added
* `pictovap plan --wordpress-post ID` reads a WordPress Gutenberg post through
  the REST API edit context and creates a visual plan without modifying the post
* Gutenberg headings and nearby section text now become Visual Brief slots and
  preserve their placement targets for a later WordPress publish step

### Changed
* Markdown is documented as a portable developer and static-site input rather
  than the only article input for Pictovap

## [0.6.0] - 2026-07-14

### Added
* `pictovap doctor` loads installed plugins and verifies selected adapter
  constructor configuration without executing CMS writes
* `pictovap plan --provider NAME` runs an independently installed image-source
  plugin through candidate validation, Fit Score, provenance, and placement planning
* `pictovap publish --cms NAME --dry-run` reconstructs and previews typed CMS
  placement operations; omitting `--dry-run` executes and validates `CMSAdapter.place`
* repeatable adapter constructor options with JSON scalar decoding and
  `KEY=@ENV_VAR` secret resolution

### Changed
* an explicitly selected provider that returns no candidates no longer falls
  back to demo data, preventing a false-positive integration result
* generated plugin packages now depend on the complete Pictovap 0.6 runtime
  and document their install-to-execution workflow

## [0.5.0] - 2026-07-14

### Added
* third-party adapter discovery through the `pictovap.image_sources` and
  `pictovap.cms` Python entry-point groups
* public `pictovap.testing` contract assertions for provider and CMS adapter packages
* `pictovap plugins` for inspecting installed adapters
* `pictovap scaffold provider|cms NAME` for generating standalone, tested plugin packages

## [0.4.0] - 2026-07-14

### Added
* provider license strings are normalized with `LicenseType`, including the
  values emitted by local, Pexels, Unsplash, DepositPhotos, and Openverse sources
* local image candidates expose JSON-safe EXIF metadata while excluding precise
  GPS information by default

### Fixed
* demo smoke tests now write into isolated temporary directories and verify the file they actually generate
* the bundled demo serializes a stable `sample-article.md` source label instead of a machine-specific `site-packages` path
* restored the complete canonical MIT license text so GitHub and package registries can identify the OSI-approved license
* package initialization now loads `create_visual_plan` lazily, removing the runtime warning from `python -m pictovap.demo`
* provenance and Unsplash metadata timestamps are timezone-aware UTC values

### Changed
* package metadata now uses the SPDX `MIT` expression and declares the shipped license file through current setuptools metadata
* **Breaking:** the supported Python floor is now 3.10 because Python 3.9 is end-of-life and
  current security-fixed Pillow, Requests, and pytest releases require 3.10
* runtime dependencies now declare security-fixed minimums; unused NumPy and
  provider SDK dependencies and the duplicate `requirements.txt` manifest were removed

## [0.3.1] - 2026-07-13

### Changed
* installation docs and the README Quickstart now lead with
  `pip install pictovap` for users, keeping the editable from-source path
  for contributors
* expanded PyPI keywords and added Issues/Changelog project URLs so the
  package page surfaces more of what the project does
* added PyPI version and Python-version badges to the README

### Removed
* dead `__main__` block in `services/wordpress.py` — unreachable in the
  installed library and it printed the configured WordPress URL/username
  to stdout

## [0.3.0] - 2026-07-12

### Changed
* **Breaking (soft):** the importable package was renamed from `pictova`
  to `pictovap`, matching the product and PyPI distribution name.
  Old imports keep working through a deprecation alias — `import pictova`
  and `from pictova.core... import ...` resolve to the same module
  objects as their `pictovap` counterparts and emit a
  `DeprecationWarning`. The alias will be removed in a future major
  version.

  Migration: replace `pictova` with `pictovap` in imports; nothing else
  changes. The `pictova` console script also remains as an alias of
  `pictovap`.
* `YOUnsplashDownloader` renamed to `UnsplashSource`, completing the
  removal of legacy "YO" branding from adapter class names

### Added
* runnable adapter examples under `examples/adapters/` (image source and
  CMS adapter skeletons that plug into the real pipeline without
  credentials)

## [0.2.2] - 2026-07-12

### Fixed
* package could not be imported on Python 3.9 (`X | Y` annotation without
  `from __future__ import annotations` in `demo.py`) despite declaring
  `requires-python >= 3.9`; CI now tests 3.9 as well
* runtime paths (`.env` lookup, post-media manifests) resolved relative to
  the installed package and landed inside site-packages for a real
  `pip install`; they now resolve from the working directory, with a
  `PICTOVA_WORKSPACE_DIR` override
* `pictova.__version__` reported 0.2.0 while the package was 0.2.1; now
  synced and guarded by a test
* `upload_media()` docstring promised slug-conflict handling that does
  not exist

### Changed
* `YOWordPressUploader` renamed to `WordPressUploader`; the HTTP
  User-Agent is now a version-aware `Pictovap-Media-Uploader/<version>`
* language detection markers replaced with general-purpose Turkish and
  English stopwords instead of topic-specific vocabulary
* CI installs the package the way PyPI users get it
  (`pip install ".[test]"` instead of an editable install), and a hygiene
  test permanently scans `src/` and `tests/` for personal-legacy leftovers

### Removed
* ~2,400 lines of dead code inherited from the legacy personal project
  (unused slug engine, unused metadata generator, unused image filter,
  hardcoded geography aliases), none of it reachable from the pipeline

## [0.2.1] - 2026-07-11

### Fixed
* missing `services/__init__.py` silently excluded the services module
  from built packages
* demo sample article only existed in a source checkout and crashed for
  installed users; it now ships as package data
* demo output path landed inside site-packages for a real install
* report generation regressed to unconditional; it is opt-in again

Note: the `v0.2.0` tag was never published to PyPI (its publish run
failed before these fixes); 0.2.1 is the first release available on PyPI.

## [0.2.0] - 2026-07-09

### Added
* credential-free demo
* public OSS README
* Visual Brief primitive
* Fit Score primitive
* Provenance Pack primitive
* CMS Placement primitive
* sample publisher profile
* example output
* CI smoke test
* public-language guard test
* open-source readiness document
* adoption playbook
* starter issue backlog

### Changed
* product identity from legacy Pictova language to Pictovap
* WordPress reframed as CMS adapter
* yoldaolmak reframed as dogfooding case
* public docs rewritten around OSS infrastructure

### Fixed
* broken docs links
* collapsed file formatting
* Makefile/demo contract
* CI install/demo smoke path
* program-specific public language

### Known limitations
* no external adoption yet
* no tagged release yet
* limited adapter coverage
* provenance is audit trail, not legal guarantee
* demo uses mock/local candidates
* package/legacy CLI compatibility still uses `pictova` in places
