**Title:** Ghost CMS placement adapter
**Type:** Discussion / feature request
**Labels:** `enhancement`, `adapter`, `discussion`

**Problem:**
Pictovap currently has a WordPress CMS adapter extracted from production use. Ghost is a popular open-source CMS, and supporting it would demonstrate that the `CMSPlacement` primitive is genuinely CMS-agnostic.

**Why it matters:** 
A second CMS adapter validates the adapter architecture. Ghost is widely used by independent publishers — Pictovap's target audience.

**Proposed approach:**
Discuss the following before starting implementation:
- Would Ghost Admin API or Content API be the right integration point?
- Should image upload and block injection be handled separately?
- Are there Ghost-specific placement patterns (e.g., cards) that need mapping?

**Acceptance criteria:**
- Discussion produces a clear implementation plan.
- If implemented: `src/pictova/publishers/ghost.py` translates `CMSPlacement` into Ghost Admin API payload with tests.

**Credentials required:** Yes (Local Ghost instance for testing)
**Difficulty:** Medium
