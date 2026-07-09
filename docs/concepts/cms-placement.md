# CMS Placement

The **CMS Placement** is the fourth and final core primitive in the Pictovap pipeline.
It is a CMS-agnostic plan describing where and how selected images should be injected
into the target publishing platform.

Pictovap does not assume any specific CMS. The `CMSPlacement` object is produced by the
core engine and consumed by a CMS-specific adapter. WordPress, Ghost, and Strapi are all
valid targets — the primitive itself is platform-neutral.

## Structure

A `CMSPlacement` contains:

- **`article_id`** — the identifier of the target article
- **`adapter_target`** — the specific adapter implementation to invoke
- **`target_platform`** — human-readable platform name (e.g., `wordpress`, `ghost`, `strapi`, `demo`)
- **`placements`** — array of `PlacementInstruction` objects

### Placement Instructions

Each `PlacementInstruction` describes one image placement:

| Field | Description |
|---|---|
| `slot_id` | Which image slot this instruction fulfills |
| `output_path` | Path to the processed image file |
| `target_section` | Section heading where the image is placed |
| `placement_strategy` | `featured`, `after_heading`, `gallery`, etc. |
| `image_role` | `featured`, `content`, or `gallery` |
| `alt_text` | Accessibility and SEO alt text |
| `caption` | Display caption |

## CMS Adapters

CMS-specific adapters (in `src/pictova/publishers/`) read the `CMSPlacement` plan
and execute the native API calls for their platform:

- **WordPress** (production-tested): uploads to media library, inserts Gutenberg image blocks
- **Ghost** (stub): reference implementation
- **Strapi** (stub): reference implementation
- **Mock** (demo): writes output to JSON, no CMS connection

WordPress is one adapter among many. Adding a new CMS target means writing a new
adapter that reads the same `CMSPlacement` plan — the core engine is unchanged.

## Example

```python
from pictova.core.primitives import CMSPlacement, PlacementInstruction

placement = CMSPlacement(
    article_id="demo-article-001",
    adapter_target="mock_adapter",
    target_platform="demo",
    placements=[
        PlacementInstruction(
            slot_id="featured",
            output_path="pictovap_minimal-backpack.webp",
            target_section="",
            placement_strategy="featured",
            image_role="featured",
            alt_text="A clean editorial image of travel packing and minimalist gear.",
            caption="The Future of Minimalist Travel: Start by choosing a versatile color palette.",
        )
    ],
)

print(placement.to_dict())
```

**Source:** `src/pictova/core/primitives.py` — `CMSPlacement` and `PlacementInstruction` classes.

See also: [Adapter Architecture](../adapters/overview.md) for how to add a new CMS target.
