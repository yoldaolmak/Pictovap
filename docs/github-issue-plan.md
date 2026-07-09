# GitHub Issue Plan

This document outlines 5 issues that should be opened manually on GitHub **after** the release is published. These issues are designed to foster external adoption and signal that the project is active and welcoming to contributors.

---

## Issue 1: Openverse source adapter
**Title:** `[ADAPTER] Add Openverse image source adapter`
**Type:** Feature / Good First Issue
**Body:**
```markdown
Currently, Pictovap relies on Unsplash and DepositPhotos for external image candidates. We need a free, completely open source of creative-commons imagery to make the default demo more robust for users who don't have API keys.

Openverse provides an excellent API for this. The task is to build a `src/pictova/providers/openverse.py` adapter that implements our standard candidate interface.
```
**Labels:** `adapter`, `good first issue`, `enhancement`
**Why it matters:** Attracts OSS-minded contributors who want to work with open data APIs and provides a clear, scoped technical task.

---

## Issue 2: Try-your-own-article feedback request
**Title:** `[FEEDBACK] Testing the default demo with your own articles`
**Type:** Discussion
**Body:**
```markdown
If you've run the local credential-free demo (`make demo`), we want to hear how it performs on your own Markdown articles!

Run:
`python -m pictova.demo --article path/to/your/article.md --profile examples/profiles/sample-publisher.yaml --output my-plan.json`

Did the `VisualBrief` correctly identify the necessary image slots based on your headings? Post your results or any parsing errors here.
```
**Labels:** `feedback`, `discussion`
**Why it matters:** Directly encourages the behavior outlined in the Adoption Playbook and lowers the barrier to first contact.

---

## Issue 3: Ghost CMS adapter discussion
**Title:** `[ADAPTER] Discussing architecture for a Ghost CMS placement adapter`
**Type:** Enhancement / Discussion
**Body:**
```markdown
Pictovap's `CMSPlacement` primitive is designed to be CMS-agnostic, but currently, we only have a reference WordPress adapter. 

Many independent publishers use Ghost. Before we build this, let's discuss how the Ghost Admin API handles image uploads vs. HTML mobiledoc insertion. If anyone here uses Ghost, how do you currently handle programmatic media?
```
**Labels:** `adapter`, `discussion`, `help wanted`
**Why it matters:** Targets a specific segment of the target audience (Ghost users) and invites architectural discussion rather than just code drops.

---

## Issue 4: Provenance Pack license confidence mapping
**Title:** `Standardize license confidence mapping for Provenance Packs`
**Type:** Refactor / Good First Issue
**Body:**
```markdown
Right now, image adapters return license information as raw strings. To make the `ProvenancePack` a true audit trail, we need to map these varying strings (e.g., "CC0", "Creative Commons Zero", "free-to-use") into a standardized `LicenseType` enum.

This will involve updating `src/pictova/core/primitives.py` and ensuring existing adapters cast to this enum.
```
**Labels:** `refactor`, `good first issue`
**Why it matters:** Shows that we take the "rights-aware" part of the product identity seriously and provides a low-risk Python refactoring task.

---

## Issue 5: External publisher sample profile request
**Title:** `[DATA] Request for diverse publisher profiles (YAML)`
**Type:** Data / Community
**Body:**
```markdown
Pictovap evaluates images based on the tone and rules defined in a Publisher Profile. We currently have examples for a travel guide (`sample-publisher.yaml`). 

We want to ensure our engine works for diverse niches (e.g., tech reviews, local news, e-commerce, recipe blogs). If you run a publication, please contribute a YAML profile defining your visual tone! You can base it on `examples/profiles/sample-publisher.yaml`.
```
**Labels:** `community`, `help wanted`
**Why it matters:** Allows non-coders (editors, publishers) to contribute meaningfully to the repository by just writing YAML.
