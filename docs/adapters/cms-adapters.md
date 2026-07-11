# CMS Adapters

CMS adapters are the final stage of the Pictovap pipeline. They read the `CMSPlacement`
plan produced by the core engine and execute the native API calls required to place
images in the target content management system.

## What a CMS Adapter Does

1. Receives a `CMSPlacement` object with an array of `PlacementInstruction` records.
2. For each instruction: upload the processed image, write alt text and caption, and
   place the image at the specified location within the article.
3. Return a structured result indicating what was placed, what failed, and why.

The adapter does not score images, generate metadata, or make editorial decisions.
Those steps happen in the core pipeline before the adapter is called.

## Existing Adapters

### WordPress / Gutenberg (`src/pictova/services/wordpress.py`)

**Status: production-tested**

`WordPressUploader.place()` uploads each image to the WordPress media
library via REST API, then inserts a Gutenberg image block at the position
matching `target_section` (by heading text). This is the most complete of
the three adapters: it is the only one that honors placement targeting
rather than always appending to the end of the post.

Required environment variables:
```
WP_URL=https://yoursite.com
WP_USER=your_user
WP_APP_PASSWORD=your_app_password
```

WordPress is one adapter among many. Nothing in the core engine is specific to WordPress.

### Ghost (`src/pictova/publishers/ghost.py`)

**Status: reference implementation, not production-tested**

`GhostPublisher.place()` uploads each image and appends it as an image card
at the end of the post's Lexical body. It does not yet honor
`target_section` or `placement_strategy` — every image lands at the bottom,
in placement order.

### Strapi (`src/pictova/publishers/strapi.py`)

**Status: reference implementation, not production-tested**

`StrapiPublisher.place()` uploads every image, but Strapi content-types are
user-defined, so this generic adapter only knows how to attach one media
field on one content-type per entry (`content_type`/`field_name`,
configurable in the constructor, default `articles`/`cover`). If a
`CMSPlacement` contains more than one instruction, every image still
uploads successfully, but only the last one wins the field — the adapter
reports this back through `place()`'s `warnings`, it does not fail silently.
Projects with a gallery/repeatable media field should subclass
`StrapiPublisher` and override `place()`.

### Mock (`src/pictova/demo.py`)

**Status: used by the credential-free demo**

Writes the `CMSPlacement` output to `examples/sample-output.json`. No CMS connection,
no credentials, no network calls.

## Writing a New CMS Adapter

1. Create a new file in `src/pictova/publishers/`, e.g. `ghost_adapter.py`.
2. Implement a class with a `place(placement: CMSPlacement) -> dict` method.
3. The method should:
   - Upload each image via the CMS's media API
   - Update the article with the placement instructions
   - Return a result dict with `placed`, `failed`, and `warnings` keys
4. Add credential documentation in `.env.example`.
5. Register the adapter in the profile system.
6. Write unit tests that mock HTTP calls and assert the placement contract.

See the [Adapter Contribution Guide](../contributing/adapters.md).

## Open Adapter Opportunities

The following CMS adapters are not yet implemented and would be valuable contributions:

- **Hugo** — static site generator with image shortcodes
- **Contentful** — headless CMS with rich media API
- **Webflow** — visual CMS with REST API
- **Directus** — headless CMS

See [Good First Issues](../contributing/good-first-issues.md) for scoped starting points.
