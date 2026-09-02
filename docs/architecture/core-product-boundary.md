# Core and Product Boundary

Pictovap Core is a public, standalone framework for making and transporting
visual editorial decisions. Commercial applications may consume Core, but Core
must remain usable by an independent developer for one article or inside a
custom pipeline.

> **Core knows visual decisions. Product knows an enterprise visual estate and
> manages its lifecycle.**

## What belongs in Core

- Visual Brief, Fit Score, Provenance Pack, and Decision Pack primitives
- publisher-profile schemas and deterministic policy inputs
- adapter protocols, reference adapters, Python API, CLI, validation, and diff
- credential-safe, side-effect-free planning and review contracts

Core never requires a hosted account, organization record, private service, or
particular CMS. A framework consumer can plan, validate, and transport a
single article without creating enterprise state.

## What does not belong in Core

- organization, site, page, section, asset, or placement inventory across an
  enterprise estate
- crawl observations, version history, findings, prioritization, or dashboards
- roles, permissions, authorization gates, queues, retries, idempotency, or
  execution receipts
- private policy evaluation, orchestration, live verification, or remediation
  engines

Those are application concerns. They may depend on Core's public contracts,
but must not be imported into, required by, or represented as hidden state in
the public framework.

## Integration rule

A product integration accepts Core's serialized contracts at a deliberate
boundary. It records its own observations and lifecycle state separately, then
may ask Core to produce or validate a visual decision. A successful Core plan
does not imply that an enterprise system authorized, executed, published, or
verified a change.
