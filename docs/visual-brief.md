# Visual Brief

The **Visual Brief** is the first core primitive in the Pictovap pipeline. It represents a structured, machine-readable extraction of a content article's visual requirements.

Instead of just blindly searching for a single generic thumbnail, Pictovap reads the article's text, headings (`H2`, `H3`), and context to build a brief.

## Structure

A `VisualBrief` object typically contains:

- **Article Title**: The main topic of the post.
- **Topic/Location**: Extracted entities indicating geographic or thematic limits.
- **Sections**: An array of headings and text blocks that might each need an inline image.
- **Required Image Slots**: How many images the layout requires (e.g., 1 featured, 3 inline).
- **Preferred Image Types**: (e.g., "landscape", "portrait", "infographic").
- **Avoid List**: Concepts or visual elements to avoid based on editorial rules.

By standardizing the request into a `VisualBrief`, different image source providers (Unsplash, local DAM) can interpret the requirements and return suitable candidates.
