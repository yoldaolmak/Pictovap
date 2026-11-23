# Pictovap Core Architecture

This is the code and responsibility map for the public `pictovap` package.
For product identity, scope, rights and authority rules see the
[Core/Product Contract](architecture/core-product-boundary.md). For
compatibility guarantees see [API Stability](../API_STABILITY.md).

## Data flow

```text
Markdown/article + publisher profile
  → Visual Brief + source-attempt evidence
  → candidate scoring and intent constraints
  → global selection + decision ledger
  → provenance and CMS placement proposal
  → validated Visual Plan
  → Decision Pack (pending → reviewed) + explain/audit/diff
  → optional external editor/CMS integration
```

The engine compiles data without user-facing output or file writes. A renderer
or CLI writes artifacts from that data. A plan or reviewed pack does not prove
an authorized CMS write or a live result. Provider errors and unknown license
rights must remain visible rather than being converted to positive evidence.

## Modules and boundaries

| Code location | Responsibility |
| --- | --- |
| `core/primitives.py`, `core/profile.py` | Visual Brief, scores, provenance, placements, publisher inputs |
| `core/adapters.py`, `core/sources.py`, `core/states.py` | Public adapter protocols, epistemic source records, explicit states |
| `engine/planner.py`, `engine/scoring.py`, `core/selection.py` | Deterministic per-article planning, scoring, global assignment |
| `intent.py`, `intent_validation.py`, `validation.py` | Proof/constraint ledger and side-effect-free plan validation |
| `decision_pack.py`, `plan_diff.py` | Portable review contract, pure review transitions, plan comparison |
| `engine/reporting.py`, `renderers/`, `app/` | Human-readable output, CLI workflow, artifact writing |
| `api.py` | Stable public planning entry point |
| `providers/` | Local, Unsplash, DepositPhotos, Openverse, Pexels image candidates |
| `services/wordpress.py`, `publishers/` | WordPress and reference Ghost/Strapi CMS adapters |
| `testing/`, `registry.py`, `plugins.py` | Contract fixtures, discovery and external-adapter integration |

The current adapters may contact providers or a CMS when explicitly invoked.
Credential isolation, path containment, transport safety, license evidence,
and safe application are adapter-specific concerns. A dry run is not a write.
Review-state transitions remain pure, and `application.status=not_applied`
is a negative sentinel, not an execution receipt.

## Deployment reality and known gaps

- The demo and golden corpus run offline on deterministic candidates. They
  prove the local pipeline, not provider uptime, a granted license, or a
  particular publisher's CMS deployment.
- WordPress has the broadest in-tree adapter behavior; Ghost and Strapi have
  mocked API tests with documented gaps. See [CMS Adapters](adapters/cms-adapters.md).
- A Gutenberg reference sidebar under `examples/wordpress-review-sidebar/`
  imports one pending pack, gathers local draft decisions and previews them
  without CMS writes. `review-pack` and `review-import` CLI commands keep
  authoritative final validation in Python Core; browser-side review is not
  a WordPress publication receipt or a proven live deployment.
- Vision-backed metadata and deterministic demo/plan metadata are separate
  paths today; the deterministic templates cover English and Turkish.

For contributor setup and verification commands use the
[Developer Guide](DEVELOPER.md). For editor-facing Decision Pack semantics
see [Decision Pack](concepts/decision-pack.md).
