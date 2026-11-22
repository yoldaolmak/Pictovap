# Pictovap Core Roadmap

**Direction:** A proof-carrying visual decision compiler for publishers:
article intent, candidate evidence, publisher policy, and CMS placement become
one explainable, reviewable plan. The [Core/Product Boundary](architecture/core-product-boundary.md)
defines what Core owns; enterprise visual-estate governance remains a separate
application, not a prerequisite for this open-source framework.

## Current user job — review an article's visual plan

A publisher should be able to provide one article, review why each candidate
fits or fails, accept or replace its proposed image (or reject the slot), and
compare the reviewed result with the original proposal **without making a CMS
change**. A separate authorized integration can later consume the result.

**Working in Core today:**

- Credential-free demo; article-derived Visual Brief; source adapters;
  deterministic scoring, global assignment, provenance, and CMS placement.
- Serializable Visual Plans, explain/audit/diff commands, and offline corpus
  validation. Missing source observations are recorded explicitly.
- Decision Pack schema 1 builder, validator, and pure review-state transition
  helper with actor/time and accept/replace/reject validation. All remain
  side-effect-free; `application.status` is `not_applied`.
- WordPress placement adapter is the broadest CMS implementation. External
  live CMS success and asset rights are **not** implied by local tests.

**Missing:** An editor-facing workflow that turns a proposed Decision Pack
into an inspectable, reviewed pack; a proposal-to-reviewed preview diff; and
a WordPress reference surface consuming those same contracts.

### Next vertical slice — complete review without CMS access

1. Use a real, non-sensitive article fixture to generate a Decision Pack and
   display proposed slots, candidate evidence, provenance, and gaps.
2. Collect accept/replace/reject decisions with actor and timestamp using
   the existing transition helper; preserve the source plan unchanged.
3. Show a clear proposal-versus-reviewed preview (including replacements,
   rejections, remaining coverage, and unresolved license/review questions).
4. Export and reload the reviewed pack. Confirm validation succeeds and
   `application.status` remains `not_applied` with no CMS/provider writes.

**Acceptance evidence:** An editor can finish and inspect a reviewed result
from an article without hand-editing JSON. A rejected/unlicensed/unbound
candidate, missing actor/time, duplicate slot decision, or attempted CMS side
effect must fail clearly. Demonstrate with fixtures and tests; request a real
editor trial separately. Do not call a successful offline run customer proof.

## After the review slice

- **Editorial policy and resilience:** versioned visual rules, alternate-image
  simulation, coverage and diversity diagnostics. Implement based on observed
  editorial failures, not speculative orchestration.
- **Reference integrations:** WordPress Plan → Review → Preview Diff first,
  then adapter capability checks and safe dry-run behavior for other CMSs.
- **Ecosystem:** harden public contracts, publish compatibility-tested external
  adapters, and collect reproducible publisher feedback before claiming
  adoption. A hosted account or MCP server is not required for Core to work.

Completed capabilities are described in the
[README](../README.md) and [API Stability](../API_STABILITY.md), not repeated
as historical delivery or CI checkpoints here.
