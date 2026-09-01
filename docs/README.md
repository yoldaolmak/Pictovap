# Pictovap Documentation

Welcome to the Pictovap documentation.

Pictovap is for content publishers who spend hours finding free images and
placing them in articles. WordPress Gutenberg is the first-class integration
today; the adapter-based core remains CMS-neutral.

It turns that manual loop into an inspectable workflow, from image search to
a reviewable publishing plan.

It reads article structure, creates a Visual Brief, evaluates candidate images with Fit Scores, records Provenance Packs, generates metadata, and prepares CMS Placement instructions.

## Navigation

### Guides

- [Quickstart](quickstart.md) — Get up and running in 5 minutes
- [WordPress Gutenberg Image Plans](tutorials/wordpress-automation.md) — Prepare and review visual plans without CMS writes
- [Using Pictovap](guides/using-pictovap.md) — The full user journey from configure to publish
- [Editor Report](guides/editor-report.md) — How humans review visual plans
- [Selection Engine](concepts/selection-engine.md) — Global, explainable image assignment and coverage diagnostics
- [Visual Plan Validation](concepts/plan-validation.md) — Validate adapter output locally and in CI
- [Plan Audit](concepts/plan-audit.md) — Review coverage, provenance, accessibility, and hand-off readiness
- [Golden Corpus Benchmark](concepts/golden-corpus.md) — Run the deterministic offline regression suite
- [Visual Intent Compiler](concepts/visual-intent-compiler.md) — Inspect intent, constraints, and decisions
- [Visual Plan Diff](concepts/plan-diff.md) — Attribute plan changes to article, profile, candidates, policy, or CMS placement
- [Decision Pack](concepts/decision-pack.md) — Carry a proposal into a review surface without applying CMS changes
- [Publisher Profiles](reference/publisher-profiles.md) — How to configure output rules
- [Image Sources](guides/image-sources.md) — Where images come from (local, Unsplash, DepositPhotos, Openverse, Pexels)
- [WordPress Setup](guides/wordpress-setup.md) — How to connect a real CMS
- [Ecosystem Integrations](ecosystem-integrations.md) — Where Pictovap fits with Markdown-to-WordPress, AI draft, CMS, and media tools

### Reference

- [CLI Reference](reference/cli.md) — Available commands and flags
- [Release Status](release-status.md) — Stable PyPI release versus unreleased `main`
- [Configuration Reference](reference/configuration.md) — Every environment variable
- [Publisher Profiles](reference/publisher-profiles.md) — The full profile schema
- [API Stability Policy](../API_STABILITY.md) — Stable, experimental, and internal integration surfaces
- [Framework Guide](framework.md) — Integrate an image source, CMS, or renderer
- [Framework Compatibility](../FRAMEWORK_COMPATIBILITY.md) — ABI v1 expectations for external adapters
- [Adapter Registry](reference/cli.md#discover-adapters) — Discover built-in and installed adapters safely
- [Roadmap](ROADMAP.md) — Visual Intent Compiler and evidence-backed ecosystem plan

### Architecture

- [Architecture](ARCHITECTURE.md) — Core primitives, adapter model, data flow
- [Adapter Overview](adapters/overview.md) — Where image source and CMS adapters live
- [Brand & Naming](architecture/naming.md) — Product name vs. package name

### Contributing

- [July 2026 Adapter Sprint](contributing/adapter-sprint.md) — Claimable integrations and public checkpoints
- [WordPress Gutenberg Mini Sprint](contributing/wordpress-gutenberg-minisprint.md) — Small fixture, test, and report contributions around image placement
- [Writing Adapters](contributing/adapters.md) — In-tree adapter contracts and checklists
- [Building Adapter Plugins](contributing/plugins.md) — Scaffold, entry points, and contract tests
- [Ecosystem Pull Requests](contributing/ecosystem-prs.md) — How to contribute to adjacent projects without link spam

Pictovap currently has no graphical user interface. It is a CLI-first open-source core. The intended review surface is an editor-readable report, while CMS adapters consume the JSON plan.
