# Pictovap Roadmap

Pictovap is becoming a **proof-carrying editorial visual compiler**. The
product is not another stock-image search or alt-text utility. It compiles
article intent, candidate evidence, publisher policy, and CMS placement into a
reviewable visual plan whose decisions can be explained later.

## Public Core scope

This roadmap is for Pictovap Core, the public framework. Core remains usable
for a single article and knows visual decisions; it does not manage an
organization's estate or operational lifecycle. Enterprise inventory, findings,
authorization, orchestration, execution receipts, and live verification belong
to a separate commercial application that consumes Core's public contracts.

```text
Article → Visual Intent Graph → Candidate Evidence → Constraints
        → Decision Ledger → Provenance Pack → CMS Placement
        → Decision Pack → Editor Review → Product integration boundary
```

## North-star contract

Every plan should answer five questions without rerunning a provider:

1. What visual job did this article section require?
2. Which hard and soft constraints were applied?
3. Why was each candidate selected, rejected, or left for review?
4. What license, source, accessibility, and processing evidence was observed?
5. What did an editor decide, without implying that a CMS application occurred?

## Phase 0 — Public foundation (complete)

- [x] Visual Brief, Fit Score, Provenance Pack, and CMS Placement primitives
- [x] Stable public Python API and adapter protocols
- [x] WordPress-first, CMS-neutral integration model
- [x] Credential-free local demo and real non-editable package smoke test
- [x] CI, security hygiene, CodeQL, dependency review, and Scorecard workflow
- [x] Contributor starter kits, standalone adapter examples, and Codespaces setup
- [x] PyPI publishing, compatibility policy, and release notes
- [x] Golden corpus benchmark across six editorial shapes
- [x] Read-only adapter registry for built-ins and installed plugins

## Phase 1 — Visual Intent Compiler (current)

This is the main product transformation. New work should strengthen this
contract before adding another provider or CMS adapter.

- [x] Visual Intent Graph derived from article structure and publisher profile
- [x] Hard/soft constraint vocabulary for license, source, dimensions, fit, CMS, and diversity
- [x] Decision Ledger with candidate evidence and global-assignment reasons
- [x] Additive `intent_proof` schema in every generated plan
- [x] `pictovap explain` read-only editor/CI report
- [x] Golden-corpus assertions for intent proof coverage
- [x] Intent proof validator with stable error codes
- [x] Plan diff: explain what changed when article, profile, or candidates change

## Phase 2 — Decision Pack and reference review surface (current)

The Decision Pack is the portable review contract. It does not duplicate the
planning engine: it groups its existing evidence by slot and records review
state. Its `not_applied` application value is a negative sentinel, not an
execution lifecycle or receipt contract. WordPress is the first reference
review surface, not the conceptual center of the framework.

- [x] Decision Pack schema 1 builder and side-effect-free validator
- [x] Explicit `pending` review and `not_applied` application states
- [ ] Editor decision receipt: accept, replace, or reject with actor and time
- [ ] Preview diff between a proposed and reviewed Decision Pack
- [ ] WordPress review surface: Plan → Review → Preview Diff
- [ ] Document the hand-off from a reviewed pack to Product-owned execution

Authorization, Apply, idempotency, rollback, execution receipts, and live
verification remain private Product responsibilities and are not future Core
Phase 2 deliverables.

## Phase 3 — Editorial policy, corpus, and resilience

- [ ] Publisher Visual Constitution: explicit, versioned visual policy YAML
- [ ] Constraint policy overrides in Publisher Profile v2
- [ ] Fallback simulation when a selected image is removed or becomes unusable
- [ ] Coverage delta and risk report for alternative assignments
- [ ] Cross-article duplicate and source-concentration policy
- [ ] CMS capability matrix for crop, caption, alt text, and media-library behavior

## Phase 4 — Integration surfaces

- [ ] CMS capability adapters for placement validation and safe dry-runs
- [ ] MCP server only after the public intent and proof contracts stabilize
- [ ] External adapter conformance badge backed by contract receipts
- [ ] Stable Framework ABI v1 after one complete compatibility cycle

## Phase 5 — Ecosystem and adoption

- [ ] Third-party adapter packages with independent CI and compatibility pins
- [ ] External publisher case studies with reproducible, non-sensitive evidence
- [ ] Contributor issue tracks for intent rules, policy fixtures, and CMS behavior
- [ ] Release cadence tied to benchmark, compatibility, and security gates

## Daily delivery rule

Each development day should deliver one bounded vertical slice:

1. one contract or behavior change
2. one regression or corpus fixture
3. one user-facing explanation or example
4. focused quality gates and a pushed commit

We will not use daily commits to inflate activity, add redundant providers, or
make unsupported adoption claims. The repository should become visibly more
useful to an editor and safer for an external adapter author after every slice.
