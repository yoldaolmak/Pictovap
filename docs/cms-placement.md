# CMS Placement

The **CMS Placement** object bridges the gap between Pictovap's visual intelligence engine and the target publishing platform.

Pictovap is CMS-agnostic. It does not assume WordPress is the target. Instead, it generates a `CMSPlacement` plan.

## The Plan

A `CMSPlacement` plan contains:
- **Target Platform**: The identifier of the CMS (e.g., `wordpress`, `ghost`, `strapi`).
- **Post ID**: The target article identifier.
- **Placements**: An array of instructions.

### Placements Array

Each placement dictates:
- The path to the processed WebP file.
- The `ProvenancePack` data (for injecting alt tags and captions).
- The injection target (e.g., `featured_image`, or `after_heading_index_2`).

CMS-specific Adapters (located in `src/pictova/publishers/`) are responsible for reading this plan, uploading the media via the CMS API, and updating the article's layout (e.g., injecting Gutenberg blocks for WordPress).
