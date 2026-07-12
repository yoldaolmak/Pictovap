**Title:** Try Pictovap with your own Markdown article
**Type:** Discussion / feedback
**Labels:** `feedback`, `help wanted`

**Problem:**
We'd like early feedback from anyone willing to try Pictovap's demo with their own Markdown article. 

**Why it matters:** 
Real-world article formats vary widely. Testing with diverse input helps identify structural extraction gaps early.

**Proposed approach:**
Anyone who is willing can:
1. Clone the repository and follow the Quickstart.
2. Run: `python -m pictovap.demo --article path/to/your/article.md --output my-plan.json`
3. Inspect the JSON output and answer:
   - Did the demo run without errors?
   - Did the Visual Brief correctly identify sections and image slots?
   - Were the Fit Scores reasonable for your content type?
   - Is the JSON output structure clear and useful?

**Acceptance criteria:**
- At least one external person has tried the demo and reported results (success or failure).

**Credentials required:** No
**Difficulty:** Low
