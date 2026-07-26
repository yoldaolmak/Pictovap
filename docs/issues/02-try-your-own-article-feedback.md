**Title:** Try Pictovap with your own Markdown article
**Type:** Discussion / feedback
**Labels:** `feedback`, `help wanted`

**Problem:**
We'd like early feedback from anyone willing to try Pictovap's demo with their own Markdown article. 

**Why it matters:** 
Real-world article formats vary widely. Testing with diverse input helps identify structural extraction gaps early.

**Proposed approach:**
Anyone who is willing can:
1. Install the current release: `python -m pip install --upgrade pictovap`
2. Run: `pictovap plan --article path/to/your/article.md --output my-plan.json --report my-plan.md`
3. Generate the safe report:
   `pictovap feedback --plan my-plan.json --format markdown`
4. Paste the generated feedback Markdown into a
   [new external validation issue](https://github.com/yoldaolmak/Pictovap/issues/new?template=external_validation.md).
   It includes safe OS/Python metadata and excludes article text, private
   paths, image URLs, profile names, and credentials.
5. Inspect the JSON and Markdown outputs and answer:
   - Did the demo run without errors?
   - Did the Visual Brief correctly identify sections and image slots?
   - Were the Fit Scores reasonable for your content type?
   - Is the report clear and useful for editorial review?

**Acceptance criteria:**
- At least one external person has tried the demo and reported results (success or failure).

**Credentials required:** No
**Difficulty:** Low
