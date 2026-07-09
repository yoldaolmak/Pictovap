# Case Study: Yoldaolmak.com

Pictovap is not just a theoretical architecture—it was extracted from the production infrastructure of [Yoldaolmak.com](https://yoldaolmak.com), a high-volume independent travel publisher.

## The Problem

Before Pictovap, the editorial team at Yoldaolmak faced a bottleneck in visual operations. A typical 2,000-word travel guide required:

1. **Analysis**: An editor reading the text to figure out what images were missing (e.g., "We need a picture of the Galata Tower here, and Turkish tea here").
2. **Sourcing**: Searching through DepositPhotos, Unsplash, or local iCloud backups to find candidates.
3. **Curation**: Rejecting images that looked too generic, had wrong aspect ratios, or were already used in a previous post.
4. **Processing**: Downloading the heavy source files, resizing them, converting to WebP, and writing SEO-optimized alt text and captions in Turkish.
5. **Placement**: Manually uploading each image into the WordPress media library and inserting Gutenberg blocks in the exact right paragraph.

This process took an average of **45 minutes per article**, completely detached from the writing process.

## The Solution

By implementing the four Pictovap primitives (`VisualBrief`, `FitScore`, `ProvenancePack`, `CMSPlacement`), Yoldaolmak fully automated this pipeline.

- The `VisualBrief` reads the drafted WordPress post via REST API, extracting geographic intent (e.g., "Istanbul") and identifying missing visual slots.
- The `FitScore` engine evaluates thousands of local and stock candidates, immediately discarding images that fail the brand's editorial constraints.
- The `ProvenancePack` ensures that Unsplash photographers receive proper attribution, and that the brand maintains a permanent audit trail of license compliance.
- The `YOWordPressUploader` adapter executes the `CMSPlacement` instructions, injecting perfectly formatted Gutenberg image blocks natively into the CMS.

## The Result

The visual finishing process went from 45 minutes of manual labor to **~30 seconds of headless computation**. Yoldaolmak editors now focus entirely on narrative quality, while Pictovap acts as their automated photo editor, researcher, and layout assistant.
