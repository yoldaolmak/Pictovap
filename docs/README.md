# Pictovap Documentation

Welcome to the Pictovap documentation.

Pictovap is an open-source image-planning and CMS placement framework for publishers.

It turns WordPress Gutenberg or Markdown articles into rights-aware visual plans.

It reads article structure, creates a Visual Brief, evaluates candidate images with Fit Scores, records Provenance Packs, generates metadata, and prepares CMS Placement instructions.

## Navigation

### Guides
- [Quickstart](quickstart.md) — Get up and running in 5 minutes
- [Using Pictovap](guides/using-pictovap.md) — The full user journey from configure to publish
- [Editor Report](guides/editor-report.md) — How humans review visual plans
- [Publisher Profiles](reference/publisher-profiles.md) — How to configure output rules
- [Image Sources](guides/image-sources.md) — Where images come from (local, Unsplash, DepositPhotos, Openverse, Pexels)
- [WordPress Setup](guides/wordpress-setup.md) — How to connect a real CMS

### Reference
- [CLI Reference](reference/cli.md) — Available commands and flags
- [Configuration Reference](reference/configuration.md) — Every environment variable
- [Publisher Profiles](reference/publisher-profiles.md) — The full profile schema

### Architecture
- [Architecture](ARCHITECTURE.md) — Core primitives, adapter model, data flow
- [Adapter Overview](adapters/overview.md) — Where image source and CMS adapters live
- [Brand & Naming](architecture/naming.md) — Product name vs. package name

### Contributing

- [July 2026 Adapter Sprint](contributing/adapter-sprint.md) — Claimable integrations and public checkpoints
- [Writing Adapters](contributing/adapters.md) — In-tree adapter contracts and checklists
- [Building Adapter Plugins](contributing/plugins.md) — Scaffold, entry points, and contract tests

Pictovap currently has no graphical user interface. It is a CLI-first open-source core. The intended review surface is an editor-readable report, while CMS adapters consume the JSON plan.
