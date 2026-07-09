**Title:** Add non-travel sample publisher profile
**Type:** Feature request
**Labels:** `enhancement`, `good first issue`, `examples`

**Problem:**
Pictovap's current examples are focused on travel blogging (the dogfooding case). To demonstrate versatility, we need at least one profile for a different content vertical — for example, e-commerce product pages, tech reviews, or recipe blogs.

**Why it matters:** 
Showing that Pictovap handles non-travel content helps potential adopters evaluate whether it fits their use case.

**Proposed approach:**
- Create a YAML profile in `examples/profiles/` (e.g., `ecommerce.yaml` or `tech-review.yaml`).
- Create a matching sample article in `examples/articles/`.
- Verify the demo runs correctly with the new profile and article.

**Acceptance criteria:**
- A new profile YAML exists in `examples/profiles/`.
- A matching sample article exists in `examples/articles/`.
- `python -m pictova.demo --article examples/articles/<new>.md --profile examples/profiles/<new>.yaml` runs without errors.
- The output demonstrates reasonable image slots for the content type.

**Credentials required:** No
**Difficulty:** Very Low
