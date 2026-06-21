# Pictova Documentation

**Pictova** — Visual Intelligence for Content

Pictova finds, selects, processes, and places images into WordPress posts from any source: free photo APIs, licensed stock providers, Mac Photos, or local files. It runs as a CLI, an HTTP service, or a Python library.

---

## Contents

### Concepts
Understand the system before running it.

- [Overview](concepts/overview.md) — What Pictova is and why it exists
- [Visual Memory](concepts/visual-memory.md) — The local image index and Mac Photos integration
- [Semantic Selection](concepts/semantic-selection.md) — How images are matched to content
- [The Pipeline](concepts/pipeline.md) — review → plan → process → attach
- [Image Sources](concepts/sources.md) — All supported providers and local sources

### Guides
Task-oriented walkthroughs.

- [Quickstart](guides/quickstart.md) — First image attached in 5 minutes
- [Installation](guides/installation.md) — Full setup with all components
- [Mac Photos Setup](guides/mac-photos-setup.md) — Index and enrich your Photos library
- [WordPress Setup](guides/wordpress-setup.md) — Credentials and site profiles
- [Adding Image Sources](guides/adding-sources.md) — Configure Unsplash, DepositPhotos, local paths

### Reference
Complete specification for all interfaces.

- [CLI Reference](reference/cli.md) — All `pictova` commands and flags
- [HTTP API Reference](reference/http-api.md) — All endpoints, payloads, and responses
- [Configuration](reference/configuration.md) — Environment variables and config file
- [Site Profiles](reference/profiles.md) — Per-site rules and customization

### Architecture
How it is built and why.

- [System Overview](architecture/overview.md) — Layers, modules, data flow
- [Native vs Legacy Engine](architecture/native-vs-legacy.md) — Two engine paths explained
- [Engine Modules](architecture/engine-modules.md) — selector, processor, publisher, quality, metadata
- [Brand & Naming Doctrine](architecture/naming.md) — Why Pictova, Meridyen ecosystem, sub-layer names

### Ops
Running Pictova in production.

- [Runbook](ops/runbook.md) — Day-to-day operation commands
- [Indexing](ops/indexing.md) — Visual memory index maintenance
- [Monitoring](ops/monitoring.md) — Health checks and observability

---

- [Changelog](../CHANGELOG.md)
- [Contributing](../CONTRIBUTING.md)
