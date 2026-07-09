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

This process took an average of **45 minutes per article**. It scaled linearly with
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

The visual finishing process went from 45 minutes of manual labor to a single
automated pipeline invocation. Editors now focus on narrative quality. Pictovap
acts as an automated photo editor, image researcher, and layout assistant.

## What This Case Study Is Not

This is a single-publisher dogfooding case study. Yoldaolmak.com uses a
WordPress/Turkish-language setup with a specific local photo library. The Pictovap
primitives and adapter architecture are designed to generalize beyond this specific
context.

The project welcomes case studies from:
- Publishers using different CMS platforms
- Publishers in different languages
- Publishers with different image source configurations

## Compatibility Note

Product name: Pictovap.
Python package and legacy CLI may remain `pictova` for backward compatibility.
The `yoldaolmak` site profile in `src/pictova/profiles/` is one example publisher
profile, not the conceptual center of the project.
