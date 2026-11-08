# Core and Product Boundary

Pictovap Core is a public, standalone framework for making and transporting
visual editorial decisions. Commercial applications may consume Core, but Core
must remain usable by an independent developer for one article or inside a
custom pipeline.

> **Core knows visual decisions. Product governs the visual estate and its lifecycle.**

## What belongs in Core

- Visual Brief, Fit Score and selection policies, Provenance Pack, Decision Pack, and CMS Placement primitives
- publisher-profile schemas and deterministic policy inputs
- adapter protocols, reference adapters, Public API, CLI, validation, explainability, and diff
- credential-safe, side-effect-free deterministic planning and review contracts

Core never requires a hosted account, organization record, private service, or
particular CMS. A framework consumer can plan, validate, and transport a
single article without creating enterprise state.

## What does not belong in Core

- Visual Estate and Field inventory (organization, site, page, section, asset, or placement) across an enterprise estate
- crawl and source observations, version history, lineage, findings, prioritization, or dashboards
- roles, permissions, operator authority, queues, retries, idempotency, or execution receipts
- private policy evaluation, orchestration, live verification, independent closure, or remediation engines

Those are application concerns. They may depend on Core's public contracts,
but must not be imported into, required by, or represented as hidden state in
the public framework.

## Responsibility and evidence matrix

| Concern | Public Core | Enterprise Product |
| --- | --- | --- |
| Article-aware image selection, explainability, provenance | Owns | May consume exported contracts |
| Portable Decision Pack, CMS Placement, adapter protocols | Owns | Integrates with explicit API/schema pins |
| Multi-page asset and placement inventory, observation history | Does not own | Owns |
| Lineage candidates, findings, priorities and operator workspace | Does not own | Owns |
| User authority, execution receipts, verification and closure | Does not own | Owns |
| Live source freshness, customer deployment, outcome validation | Cannot infer from a plan | Must demonstrate separately |

The public Python distribution is `pictovap`; the separate enterprise
implementation is not distributed as part of that package. The names may
share a brand, but their implementation status, tests, data freshness and
customer claims are never interchangeable.

## Integration rule

A product integration accepts Core's serialized contracts at a deliberate
boundary. It records its own observations and lifecycle state separately, then
may ask Core to produce or validate a visual decision. A successful Core plan
does not imply that an enterprise system authorized, executed, published, or
verified a change.

## Scope discipline

Core makes no multi-page visual-estate, lineage-inference, or live-execution
claims. It provides portable, deterministic visual-decision primitives that an
enterprise product integration may consume.
