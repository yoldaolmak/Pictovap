# Changelog

## [0.13.0] - Unreleased

### Added

- Added a deterministic golden-corpus benchmark covering six editorial shapes.
- Added `pictovap benchmark` for offline JSON or Markdown compatibility receipts.
- Added the Framework ABI v1 compatibility summary for external adapter authors.
- Added a read-only adapter registry for built-in sources, CMS adapters,
  renderers, and installed third-party plugins.
- Added the experimental Visual Intent Compiler: proof-carrying intent graphs,
  hard/soft constraints, candidate evidence, and the `pictovap explain` report.
- Added side-effect-free intent-proof validation with machine-readable
  `intent_*` error codes and an 8-check golden-corpus proof gate.
- Added `diff_visual_plans()` and `pictovap diff` for deterministic,
  side-effect-free comparison of article identity, profile, candidate, intent,
  provenance, and CMS-placement changes.
- Added `--fail-on-change` for CI drift gates while keeping editorial plan
  differences reviewable by default.

### Changed

- Extracted the planning pipeline out of `pictovap.demo` into a silent,
  side-effect-free engine: `engine/planner.py` (plan construction),
  `engine/scoring.py` (Fit Score), and `engine/reporting.py` (editor report
  and artifact writing). The engine prints nothing and writes no files.
- The demo's terminal walkthrough is now rendered from the returned plan
  instead of being printed during planning, so the screen and the artifact can
  no longer disagree. This corrects the license line, which previously showed a
  Python enum (`LicenseType.CC0`) where the plan records `cc0`.
- `pictovap.api` no longer suppresses engine output with `redirect_stdout`; the
  engine has no output to suppress.
- The plan artifact is labelled `Pictovap Visual Plan` instead of
  `Pictovap Visual Finishing Demo`. A run that used fixture candidates is still
  identified honestly by `runtime.provider.mode`.
- Candidate fixtures moved to `pictovap.data.demo_candidates`. The engine holds
  no fixture of its own: a caller that supplies no fallback pool gets an
  honestly empty plan.
- Regenerated the committed example plans, which had been left on an older
  schema without `intent_proof` or `planning_diagnostics`.

### Fixed

- Decision Pack proposals now fail closed when the selected candidate,
  provenance, and placement evidence do not bind to the same candidate, slot,
  and generated filename.
- `accept` can no longer approve an empty proposal, and `replace` now requires
  a different scored candidate with complete replacement provenance and
  placement evidence.
- Clarified that execution receipts, idempotency, rollback, and live
  verification are Product-owned lifecycle concerns rather than Core roadmap
  deliverables.

### Removed

- Removed the duplicate `pictovap.demo.create_visual_plan()` and
  `pictovap.demo.create_wordpress_visual_plan()`. `pictovap.api` is the single
  planning API; `pictovap.demo` was already documented as internal.
- Removed the deprecated compatibility namespace and duplicate console entry
  point. The distribution now ships only the canonical `pictovap` package and
  CLI.
- Standardized runtime path overrides as `PICTOVAP_WORKSPACE_DIR`,
  `PICTOVAP_POST_MANIFEST_DIR`, and `PICTOVAP_VIL_DIR`.

- Added `audit_visual_plan()` and `pictovap audit` for a read-only editorial
  and integration readiness report.
- Audit reports expose coverage, review-queue, provenance/license,
  accessibility, and duplicate-selection checks in JSON or Markdown.
- Strict audit mode turns unresolved editorial warnings into a CI failure.

## [0.12.0] - 2026-08-10

### Added

* Standalone adapter scaffolds now include a minimal Makefile and GitHub Actions
  workflow, so a new external package has a working CI gate immediately.
* Added `pictovap.testing.sample_candidate()` as a deterministic provider
  response fixture for third-party adapter tests.

### Changed

* Generated provider and CMS packages now target the current public contract
  (`pictovap>=0.11.0`) and explicitly implement their adapter protocols.
* Scaffold README and tests now show the complete contract-check loop, including
  the bounded provider exercise path.

## [0.11.0] - 2026-08-08

### Added

* Added the public `validate_visual_plan()` API for checking serialized plans
  without network access, credentials, or a live CMS.
* Added `pictovap validate --plan` with machine-readable contract results for
  adapter CI and external integrations. `--strict` promotes recommended
  consistency warnings to failures.

## [0.10.1] - 2026-08-06

### Added

* Selection diagnostics now list the candidate pairs that crossed the visual
  similarity threshold, including their similarity ratio and applied penalty.

## [0.10.0] - 2026-08-05

### Added

* Added deterministic perceptual fingerprints for local images and an
  optional `visual_fingerprint` adapter field.
* Added diversity-aware global assignment: near-duplicate candidates can be
  penalized during selection without downloading remote assets.

### Changed

* Planning diagnostics now expose `adjusted_total_score` and
  `diversity_penalty`, making the editorial variety trade-off auditable.
* The local image source computes fingerprints opportunistically and remains
  fully compatible with adapters that do not provide one.
* Corrected the requests lower bound so a clean PyPI/wheel installation can
  resolve the published dependency set.
* Corrected the Pillow lower bound to the installable runtime baseline used by
  the image fingerprint implementation.

## [0.9.0] - 2026-08-02

### Added

* Markdown Visual Brief parsing now preserves a safe, JSON-compatible YAML
  frontmatter mapping for tags, categories, audience, location, and editorial
  constraints.
* `pictovap ecosystem explain` and `pictovap ecosystem match` generate
  copyable integration packets for adjacent Markdown-to-WordPress, AI draft,
  media upload, Gutenberg, CMS automation, and static-site migration projects.
* Ecosystem integration docs now include the supported boundary, external PR
  checklist, and a Markdown-to-WordPress pre-publish workflow example.
* The core planner now exposes a deterministic maximum-weight assignment
  engine through `SelectionPolicy`, `SelectionResult`, and
  `select_assignments`.

### Changed

* Contributor entry docs now prioritize the current no-claim
  WordPress/Gutenberg issues, link the live no-claim queue, and point
  first-time contributors to Codespaces.
* New first-PR kits give contributors exact files, focused checks, PR-size
  limits, and boundaries for the current WordPress/Gutenberg no-claim issues.
* The reusable external tester message now sends validation reports to the
  dedicated issue form instead of the legacy shared feedback thread.
* Visual plans now select candidates globally, avoid accidental image reuse by
  default, and include coverage, unfilled-slot, and policy diagnostics.
* Frontmatter context now participates in deterministic candidate relevance
  scoring and appears in Markdown editor reports.

## [0.8.0] - 2026-08-01

### Added

* A constraint-aware core selection engine maximizes total fit across all
  editorial slots instead of making independent greedy choices.
* Planning diagnostics make assignment quality machine-readable for editors,
  adapters, and downstream validation tools.

## [0.7.14] - 2026-07-26

### Changed

* Generated external validation Markdown now links directly to the dedicated
  GitHub issue form, making real downstream reports easier to submit, count,
  and review.
* Public validation docs now route testers to a new external validation issue
  instead of a shared tracking issue comment thread.

## [0.7.13] - 2026-07-26

### Added

* `make contributor-smoke` verifies the installed CLI, credential-free demo,
  and anonymous feedback report before contributors run the full local gate.

### Changed

* Anonymous feedback Markdown now includes coarse OS metadata automatically,
  reducing manual edits for external validation reports.
* External validation docs now use a PyPI-first install path and the safe
  Markdown feedback report, reducing friction for downstream usage reports.
* Contributor-facing setup docs, issue-copy templates, and the pull-request
  checklist now point to the same `make install`, `make contributor-smoke`,
  and `make contribution-check` path used by CI.
* Demo sample JSON outputs now match the current credential-free CLI demo
  contract, including runtime provider metadata and normalized license values.
* WordPress setup documentation now separates credential-free local planning
  from live WordPress reads, media uploads, and post updates.

### Fixed

* Root `.gitignore` no longer contains Markdown fence artifacts or the obsolete
  package-data exception, so packaged `src/pictovap/data` sample files
  remain addable while Python caches stay ignored.
* `python -m pictovap` now runs the public CLI entry point directly.

## [0.7.12] - 2026-07-23

### Added

* A runnable standalone Hugo CMS adapter reference demonstrates path-contained,
  idempotent static-site shortcode placement without requiring credentials.
* `pictovap feedback --format markdown` renders the anonymous validation
  summary as a GitHub issue-ready report.
* A dedicated external validation issue template asks for safe runtime and plan
  counts without article text, paths, image URLs, or credentials.

### Fixed

* GitHub Codespaces now installs the complete contributor gate dependencies,
  including lint and type-check tools, instead of only the test extra.
* New adapter and renderer packages now declare the current `pictovap>=0.7.8`
  runtime floor instead of an obsolete pre-contract minimum.
* Adoption and issue-plan drafts now use the canonical `pictovap plan` command
  and clearly mark historical issue text as non-reopenable.

## [0.7.11] - 2026-07-22

### Fixed

* CMS scaffolds can now be discovered, doctored, and conformance-checked
  without credentials; missing CMS configuration remains an explicit warning
  until the contributor implements the transport.

## [0.7.10] - 2026-07-22

### Fixed

* Adapter scaffolds no longer duplicate contract suffixes for names such as
  `contributor-source` or `hugo-adapter`.

## [0.7.9] - 2026-07-22

### Added

* `pictovap feedback --plan` creates an anonymous validation summary with safe
  runtime and plan counts for copy-pasteable external issue reports.

## [0.7.8] - 2026-07-22

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
* Standardized the importable package, console script, product, and PyPI
  distribution identity as `pictovap`.
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
  `PICTOVAP_WORKSPACE_DIR` override
* The package version reported 0.2.0 while the distribution was 0.2.1; now
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
* standardized product identity as Pictovap
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
