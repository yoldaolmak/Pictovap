# Pictovap Documentation

Pictovap Core prepares explainable visual plans for individual articles.
Choose the path matching your task; the [README](../README.md) explains
current capabilities and runnable commands.

## Evaluate a decision

- [Visual Intent Compiler](concepts/visual-intent-compiler.md) — constraints,
  candidate evidence, and assignment reasons
- [Decision Pack](concepts/decision-pack.md) — proposal and editor review
- [Plan Audit](concepts/plan-audit.md) and [Plan Diff](concepts/plan-diff.md)
- [Golden Corpus](concepts/golden-corpus.md) — offline regression cases

## Use it for publishing

- [Quickstart](quickstart.md) and [Using Pictovap](guides/using-pictovap.md)
- [Image Sources](guides/image-sources.md) and
  [WordPress Setup](guides/wordpress-setup.md)
- [CLI Reference](reference/cli.md),
  [Publisher Profiles](reference/publisher-profiles.md), and
  [Configuration](reference/configuration.md)

A plan is not an authorization, licensed purchase, CMS publication,
or independently verified outcome.

## Extend the framework

- [Core/Product Contract](architecture/core-product-boundary.md) — ownership
  of article decisions versus enterprise operations
- [Architecture](ARCHITECTURE.md),
  [Public API Stability](../API_STABILITY.md), and
  [Framework Compatibility](../FRAMEWORK_COMPATIBILITY.md)
- [Adapter protocols](adapters/overview.md),
  [Plugin authoring](contributing/plugins.md), and
  [CMS adapter limits](adapters/cms-adapters.md)
- [Developer Guide](DEVELOPER.md) — setup, commands, test gates
- [Roadmap](ROADMAP.md) — current user workflow and next slice

There is no shipped graphical editor yet. Core is usable through its
CLI and Python API; WordPress has the broadest in-tree CMS integration.
