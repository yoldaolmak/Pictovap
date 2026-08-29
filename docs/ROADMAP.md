# Pictovap Roadmap

Pictovap is becoming a **proof-carrying editorial visual compiler**. The
product is not another stock-image search or alt-text utility. It compiles
article intent, candidate evidence, publisher policy, and CMS placement into a
reviewable visual plan whose decisions can be explained later.

```text
Article → Visual Intent Graph → Candidate Evidence → Constraints
        → Decision Ledger → Provenance Pack → CMS Placement → Editor Review
```

## North-star contract

Every plan should answer five questions without rerunning a provider:

1. What visual job did this article section require?
2. Which hard and soft constraints were applied?
3. Why was each candidate selected, rejected, or left for review?
4. What license, source, accessibility, and processing evidence was observed?
5. What should the CMS place, and what is the safest fallback if an image is unavailable?

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
- [ ] Constraint policy overrides in Publisher Profile v2
- [x] Plan diff: explain what changed when article, profile, or candidates change

## Phase 2 — Editorial policy and resilience

- [ ] Publisher Visual Constitution: explicit, versioned visual policy YAML
- [ ] Fallback simulation when a selected image is removed or becomes unusable
- [ ] Coverage delta and risk report for alternative assignments
- [ ] Cross-article duplicate and source-concentration policy
- [ ] CMS capability matrix for crop, caption, alt text, and media-library behavior

## Phase 3 — Evidence-backed VisualDNA

VisualDNA is deliberately downstream of explicit policy and real editorial
feedback. It must not pretend to learn a publisher's taste from a tiny or
unverified corpus.

- [ ] Opt-in editor feedback receipt: accepted, replaced, rejected, and reason
- [ ] Aggregate visual preference report with provenance-safe statistics
- [ ] Suggested policy changes requiring maintainer/editor approval
- [ ] Optional VisualDNA profile generated only from approved feedback
- [ ] Reproducible evaluation set for any learned or heuristic preference

## Phase 4 — Integration surfaces

- [ ] WordPress review surface that consumes `intent_proof` without re-scoring
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
