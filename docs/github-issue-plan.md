# GitHub Issue Plan

These issues are ready to be opened manually on GitHub after the v0.2.0 release. Do not open them before the release tag is published.

---

## 1. Add Openverse image source adapter

**Title:** feat: Add Openverse image source adapter

**Issue type:** Feature request

**Labels:** `enhancement`, `good first issue`, `adapter`

**Body:**

Pictovap currently supports Unsplash, DepositPhotos (stub), and a local visual memory database as image sources. Openverse is a large, free, CC-licensed image search API maintained by WordPress.org that would expand the candidate pool significantly.

**Scope:**
- Implement `src/pictovap/providers/openverse.py` following the existing provider interface.
- Handle pagination and rate limiting.
- Map results to Pictovap's `candidate` model (source path, metadata, license info).
- Add unit tests with mock responses.

**Why it matters:** Adds a high-quality, free image source that doesn't require paid API keys, lowering the barrier for new users to run Pictovap with real (non-mock) candidates.

**Acceptance criteria:**
- Adapter connects to the Openverse API and returns candidates.
- Pagination is handled for queries returning many results.
- License information is mapped into the Provenance Pack format.
- Unit tests pass with mocked API responses.
- The adapter is registered in `src/pictovap/config.py`.

---

## 2. Try-your-own-article feedback request

**Title:** feedback: Try Pictovap with your own Markdown article

**Issue type:** Discussion / feedback

**Labels:** `feedback`, `help wanted`

**Body:**

We'd like early feedback from anyone willing to try Pictovap's demo with their own Markdown article.

**Steps:**
1. Clone the repository and follow the [Quickstart](README.md#quickstart).
2. Run: `python -m pictovap.demo --article path/to/your/article.md --output my-plan.json`
3. Inspect the JSON output.

**What we'd like to know:**
- Did the demo run without errors?
- Did the Visual Brief correctly identify sections and image slots?
- Were the Fit Scores reasonable for your content type?
- Is the JSON output structure clear and useful?

Any feedback — even "it crashed on my file" — is valuable at this stage.

**Why it matters:** Real-world article formats vary widely. Testing with diverse input helps identify structural extraction gaps early.

**Acceptance criteria:**
- At least one external person has tried the demo and reported results (success or failure).

---

## 3. Ghost CMS adapter discussion

**Title:** discussion: Ghost CMS placement adapter

**Issue type:** Discussion / feature request

**Labels:** `enhancement`, `adapter`, `discussion`

**Body:**

Pictovap currently has a WordPress CMS adapter extracted from production use. Ghost is a popular open-source CMS, and supporting it would demonstrate that the `CMSPlacement` primitive is genuinely CMS-agnostic.

**Questions for discussion:**
- Would Ghost Admin API or Content API be the right integration point?
- Should image upload and block injection be handled separately?
- Are there Ghost-specific placement patterns (e.g., cards) that need mapping?

**Why it matters:** A second CMS adapter validates the adapter architecture. Ghost is widely used by independent publishers — Pictovap's target audience.

**Acceptance criteria:**
- Discussion produces a clear implementation plan.
- If implemented: `src/pictovap/publishers/ghost.py` translates `CMSPlacement` into Ghost Admin API payload with tests.

---

## 4. Provenance Pack license confidence mapping

**Title:** feat: Add license confidence mapping to Provenance Pack

**Issue type:** Feature request

**Labels:** `enhancement`, `good first issue`, `core`

**Body:**

Different image APIs return licenses in different string formats (e.g., `"cc0"`, `"CC0 1.0"`, `"creative_commons"`, `"unsplash"`). Pictovap currently passes these as raw strings. A unified `LicenseType` enum would make license handling more reliable and auditable.

**Scope:**
- Define a `LicenseType` enum in `src/pictovap/core/primitives.py`.
- Map common license strings from supported providers to the enum.
- Update the Provenance Pack to use `LicenseType` instead of raw strings.
- Add unit tests for mapping edge cases.

**Why it matters:** License handling is safety-critical for publishers. A unified enum reduces the risk of misclassified licenses and makes the Provenance Pack more trustworthy as an audit trail.

**Acceptance criteria:**
- `LicenseType` enum covers at least: `CC0`, `CC_BY`, `CC_BY_SA`, `CC_BY_NC`, `UNSPLASH`, `EDITORIAL`, `UNKNOWN`.
- Existing providers map their license strings to the enum.
- Provenance Pack stores the enum value.
- Unit tests cover known license string variants.

---

## 5. External publisher sample profile request

**Title:** feat: Add non-travel sample publisher profile

**Issue type:** Feature request

**Labels:** `enhancement`, `good first issue`, `examples`

**Body:**

Pictovap's current examples are focused on travel blogging (the dogfooding case). To demonstrate versatility, we need at least one profile for a different content vertical — for example, e-commerce product pages, tech reviews, or recipe blogs.

**Scope:**
- Create a YAML profile in `examples/profiles/` (e.g., `ecommerce.yaml` or `tech-review.yaml`).
- Create a matching sample article in `examples/articles/`.
- Verify the demo runs correctly with the new profile and article.

**Why it matters:** Showing that Pictovap handles non-travel content helps potential adopters evaluate whether it fits their use case.

**Acceptance criteria:**
- A new profile YAML exists in `examples/profiles/`.
- A matching sample article exists in `examples/articles/`.
- `python -m pictovap.demo --article examples/articles/<new>.md --profile examples/profiles/<new>.yaml` runs without errors.
- The output demonstrates reasonable image slots for the content type.
