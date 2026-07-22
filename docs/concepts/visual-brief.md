# Visual Brief

The **Visual Brief** is the first core primitive in the Pictovap pipeline.
It represents a structured, machine-readable extraction of a content article's visual requirements.

Instead of treating every article as a generic image search query, Pictovap reads the
article's text, headings (H2, H3), and context to build a brief describing exactly
what imagery is needed and where.

## Structure

A `VisualBrief` object contains:

- **Article Title** — the main topic of the post.
- **Topic** — extracted thematic focus (e.g., "minimalist travel", "urban architecture").
- **Detected Location** — geographic entity if present (e.g., "Istanbul", "Sinop").
- **Article Language** — ISO language code (e.g., `en`, `tr`).
- **Sections** — array of headings and their hierarchy level (`h2`, `h3`).
- **Image Slots** — how many images the layout requires, each with:
  - `slot_id` — unique identifier within the article
  - `purpose` — `featured_image`, `inline_after_<heading>`, etc.
  - `preferred_type` — `landscape`, `portrait`, or `any`
  - `target_heading` — the section heading this slot serves
- **Avoid List** — concepts or visual elements to reject based on editorial rules.
- **Editorial Notes** — free-form guidance from the publisher profile.
- **Confidence** — how certain the parser is about the extracted brief (0.0–1.0).

## How It Is Built

Pictovap builds a `VisualBrief` using a deterministic rule-based parser:

1. Parse the article for H1 (title), H2, and H3 headings.
2. Detect language based on simple word-markers (e.g. Turkish vs. English). If markers are ambiguous, fall back to the publisher profile language.
3. Generate one featured image slot from the title.
4. Generate one inline slot per H2 section, extracting the section's first few sentences as `section_excerpt` context.
5. Apply publisher profile editorial preferences and avoid lists.

This parser does not call any AI API. It is pure Python, stateless, and testable. Language detection is deterministic and simple; future iterations might introduce more advanced NLP detection models if required.

```python
from pictovap.core.primitives import VisualBrief

brief = VisualBrief.from_markdown("examples/articles/travel-guide.md")
print(brief.article_title)   # "The Future of Minimalist Travel"
print(brief.article_language) # "en"
print(len(brief.image_slots)) # 4 (featured + 3 section slots)
print(brief.image_slots[1]["section_excerpt"]) # First few sentences context
```

## Where It Goes

The `VisualBrief` feeds into the `FitScore` stage, where candidate images are evaluated
against each slot's requirements.

**Source:** `src/pictovap/core/primitives.py` — `VisualBrief` class.

## Compatibility Note

Product name: Pictovap.
The Python package is `pictovap` (since 0.3.0); `pictova` remains a deprecated alias.
