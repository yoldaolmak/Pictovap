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
  helper with actor/time and accept/replace/reject validation.
- Development CLI: interactive `pictovap review` and read-only
  `review-preview`. The source plan stays unchanged, decisions are stored,
  rejected candidates cannot be replacements, and license uncertainty remains
  visible. No provider or CMS call occurs in the review.
- WordPress placement adapter is the broadest CMS implementation. External
  live CMS success and asset rights are **not** implied by local tests.

**Now implemented in a reference plugin:** An import-only Gutenberg sidebar
for the current post, per-slot accept/reject/replacement decisions, an
in-browser draft preview, and a downloaded decisions file. Python Core
verifies the exact original pack and review decisions via SHA-256 before it
produces a reviewed Decision Pack. No CMS writes or automatic image fetching.

**One-click alternative selection now available:** New plans contain
source-backed alternative candidate evidence. The reference sidebar displays
eligible choices and their rights status, and Python Core rejects modified or
invented replacement evidence. Older packs remain readable and can still
accept independently supplied atomic evidence.

**Local visual comparison:** The reference Gutenberg sidebar accepts
explicitly selected local image files for proposal/alternative candidates,
checks the recorded filename and image signature, and displays temporary
browser-only image previews. Image `blob:` URLs are revoked on replacement,
pack import or unmount; source URLs are never fetched for this feature.

**Real Gutenberg acceptance proven:** An authorized editor session on an
existing Gutenberg post verified sidebar registration, post-ID binding,
one-click alternatives, rights evidence display, local visual comparison
without upload, draft decisions export, Core review-import validation,
negative security rejection (wrong post, forged replacement, tampered
fingerprint, unauthorized user), and zero WordPress post/media mutations.

**Still missing:** Independent proof that a chosen local file matches the
actual provider asset, live editorial feedback on production sites, and
separately authorized publish execution.

### Next vertical slice — editorial policy and resilience

1. Editorial policy and resilience: versioned visual rules, alternate-image
   simulation, coverage and diversity diagnostics based on observed failures.
2. Observe live production editors comparing local proposal and alternative
   images across diverse post templates and themes.
3. Reference integrations: WordPress Plan → Review → Preview Diff first, then
   adapter capability checks and safe dry-run behavior for other CMSs.

**Acceptance evidence:** A publisher can make and inspect decisions without
editing decision JSON, cannot select a hard-rejected or unbound replacement,
and sees outstanding rights questions. The WordPress reference must pass
mocked Gutenberg fixtures before any live, permissioned trial. Local CI
and a real editor's successful review are distinct evidence.

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
