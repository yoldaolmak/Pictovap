# Pictovap Product Contract and Core Boundary

**Pictovap** helps publishers decide which images belong in an article, why,
and where those images could be placed. Editors need decisions they can review
and explain, with visible source and license uncertainty, instead of repeating
an opaque image-selection process for every page.

**Founding boundary:** Core knows visual decisions. Product governs the
visual estate and its lifecycle.

## Public Core

The public, independently usable Python package `pictovap` handles a single
article: Visual Brief, Fit Score, candidate evidence, provenance, intent proof,
Decision Pack, CMS Placement, explanations, validation, and adapter contracts.
Planning must not require an organization account, hosted service, enterprise
database, or specific CMS. WordPress is a reference integration, not the
framework's identity.

A source/license record describes observed evidence, **not** an automatic
purchase, rights grant, or legal approval. A proposed or reviewed plan is
**not** proof of CMS authorization, application, publication, or verification.
An adapter may perform a separately authorized action; that action needs its
own result and must not be inferred from the plan.

## Separate Enterprise Product

The commercial Product may consume versioned Core contracts while owning
multi-page/site visual inventory, observations over time, lineage candidates,
findings, operator roles, permissions, orchestration, idempotency, execution
receipts, and independent live verification. These capabilities are neither
implemented nor accepted merely because Core passes an offline test.

The Product cannot silently grant authority to discovered behaviors or
treat review state as an execution receipt. Keep the data, identity, and
authority boundaries explicit at integration points.

## Scope and evidence

| Concern | Core | Enterprise Product |
| --- | --- | --- |
| One-article visual decisions, evidence, and portable review | Owns | Consumes explicit contracts |
| CMS adapter interface and placement proposal | Owns | Authorizes and verifies its operations |
| Site-wide history, user authority, execution lifecycle | Does not own | Owns |
| Real publisher outcomes | Cannot infer | Must verify independently |

Architecture and implementation locations: [Architecture](../ARCHITECTURE.md).
Public compatibility commitments: [API Stability](../../API_STABILITY.md).
Current priorities: [Roadmap](../ROADMAP.md).
