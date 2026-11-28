# Framework and Product Boundary

**ActoVisio Framework** helps publishers decide which images belong in an article, why,
and where those images could be placed. Editors need decisions they can review
and explain, with visible source and license uncertainty, instead of repeating
an opaque image-selection process for every page.

**Founding boundary:** Framework owns visual decisions. Product governs the
visual estate and its lifecycle.

## Open-core commercial strategy

ActoVisio Framework (formerly Pictovap Framework) is public under the MIT
license. Release 0.14.0 uses `actovisio-framework` (distribution and CLI) and
`actovisio_framework` (import). The published `pictovap` 0.13.0 and a separate
legacy compatibility distribution preserve existing integration paths.
The shared display-brand root does not make Framework a free tier of the
separate enterprise application. Its strategic role is
distribution, adoption, interoperability, and technical reputation. The
separate private Enterprise Product is the commercial offering. Existing MIT
rights remain intact; Framework is not an exclusive proprietary licensing asset.

The approved target is a one-way dependency: ActoVisio builds on
ActoVisio Framework through a released, version-pinned public API. Framework
owns shared visual decision contracts and their implementation; Product owns
enterprise intelligence, state, authority, execution and verification. The
Framework must remain independently usable without Product. A historical
compatible copy may be retained only for evidenced replay needs, never as a
second evolving implementation. Enterprise-only IP stays private.

Dependency migration is an engineering acceptance gate, not an assertion that
existing Product installations already use Framework.

## Framework

The public, independently usable Python package `actovisio_framework` handles a single
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

## Product

Product consumes shared Framework contracts and owns
multi-page/site visual inventory, observations over time, lineage candidates,
findings, operator roles, permissions, orchestration, idempotency, execution
receipts, and independent live verification. These capabilities are neither
implemented nor accepted merely because Framework passes an offline test.

The Product cannot silently grant authority to discovered behaviors or
treat review state as an execution receipt. Keep the data, identity, and
authority boundaries explicit at integration points.

## Scope and evidence

| Concern | Framework | Product |
| --- | --- | --- |
| One-article visual decisions, evidence, and portable review | Owns | Consumes the versioned public API |
| CMS adapter interface and placement proposal | Owns | Authorizes and verifies its operations |
| Site-wide history, user authority, execution lifecycle | Does not own | Owns |
| Real publisher outcomes | Cannot infer | Must verify independently |

Architecture and implementation locations: [Architecture](../ARCHITECTURE.md).
Public compatibility commitments: [API Stability](../../API_STABILITY.md).
Current priorities: [Roadmap](../ROADMAP.md).
