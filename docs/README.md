# Pictovap Documentation

Welcome to the Pictovap documentation.

Pictovap is an open-source visual finishing engine for content publishers.

It turns unfinished articles into visually complete, rights-aware, publish-ready CMS pages.

It reads article structure, creates a Visual Brief, evaluates candidate images with Fit Scores, records Provenance Packs, generates metadata, and prepares CMS Placement instructions.

## Navigation

### Guides
- [Quickstart](quickstart.md) — Get up and running in 5 minutes
- [Using Pictovap](guides/using-pictovap.md) — The full user journey from configure to publish
- [Editor Report](guides/editor-report.md) — How humans review visual plans
- [Publisher Profiles](reference/publisher-profiles.md) — How to configure output rules
- [Image Sources](guides/image-sources.md) — Where images come from (local, Unsplash, DepositPhotos)
- [WordPress Setup](guides/wordpress-setup.md) — How to connect a real CMS

### Reference
- [CLI Reference](reference/cli.md) — Available commands and flags
- [Configuration Reference](reference/configuration.md) — Every environment variable
- [Publisher Profiles](reference/publisher-profiles.md) — The full profile schema

### Architecture
- [Architecture](ARCHITECTURE.md) — Core primitives, adapter model, data flow
- [Adapter Overview](adapters/overview.md) — Where image source and CMS adapters live
- [Brand & Naming](architecture/naming.md) — Product name vs. package name

Pictovap currently has no graphical user interface. It is a CLI-first open-source core. The intended review surface is an editor-readable report, while CMS adapters consume the JSON plan.
