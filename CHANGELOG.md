# Changelog

## [Unreleased]

### Fixed
* demo smoke tests now write into isolated temporary directories and verify the file they actually generate
* the bundled demo serializes a stable `sample-article.md` source label instead of a machine-specific `site-packages` path
* restored the complete canonical MIT license text so GitHub and package registries can identify the OSI-approved license
* package initialization now loads `create_visual_plan` lazily, removing the runtime warning from `python -m pictovap.demo`
* provenance and Unsplash metadata timestamps are timezone-aware UTC values

### Changed
* package metadata now uses the SPDX `MIT` expression and declares the shipped license file through current setuptools metadata
* provider license strings are normalized with `LicenseType` in provenance records
* the supported Python floor is now 3.10 because Python 3.9 is end-of-life and
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
