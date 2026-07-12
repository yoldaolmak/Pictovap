# Case Study: Yoldaolmak.com

Pictovap was extracted from the production infrastructure of
[Yoldaolmak.com](https://yoldaolmak.com), a high-volume independent travel publisher.
This case study documents the problem that motivated the project and the architecture
that solved it.

## The Problem

Before Pictovap, the editorial workflow at Yoldaolmak had a bottleneck in visual operations.
A typical 2,000-word travel guide required:

1. **Analysis** — an editor reading the text to identify missing images
   (e.g., "We need a photo of the Galata Tower here, and Turkish tea here").
2. **Sourcing** — searching through DepositPhotos, Unsplash, or local photo archives
   to find candidates.
3. **Curation** — rejecting images that looked too generic, had wrong aspect ratios,
   or had already been used in a previous post.
4. **Processing** — downloading heavy source files, resizing them, converting to WebP,
   and writing SEO-optimized alt text and captions in Turkish.
5. **Placement** — manually uploading each image to the WordPress media library and
   inserting Gutenberg blocks at the correct paragraph.

This process could take tens of minutes per long-form travel article. It scaled linearly with
article volume and was entirely manual.

## The Solution

By implementing the four Pictovap primitives, Yoldaolmak automated this pipeline:

- The `VisualBrief` reads the drafted article content, extracting geographic intent
  (e.g., "Istanbul") and identifying missing visual slots per section.
- The `FitScore` engine evaluates candidate images deterministically, discarding images
  that fail the brand's editorial constraints (forbidden patterns, license requirements,
  resolution thresholds).
- The `ProvenancePack` tracks image origin, license, and processing actions, maintaining
  an audit trail for every placed image.
- The WordPress adapter reads the `CMSPlacement` plan and injects Gutenberg image blocks
  natively into the CMS.

## The Result

Before Pictovap, visual finishing could take tens of minutes per long-form travel article. Pictovap turns that workflow into a single pipeline run, but results still require editorial review before publishing.

## What This Case Study Is Not

This is a single-publisher dogfooding case.
It is not evidence of broad external adoption.
The reusable part is the primitive/adapters model.
The site-specific part is WordPress, Turkish-language metadata, and yoldaolmak's editorial profile.

The project welcomes case studies from:
- Publishers using different CMS platforms
- Publishers in different languages
- Publishers with different image source configurations

## Compatibility Note

Product name: Pictovap.
The Python package is `pictovap` (since 0.3.0); `pictova` remains a deprecated alias.
The `yoldaolmak` site profile in `src/pictovap/profiles/` is one example publisher
profile, not the conceptual center of the project.
