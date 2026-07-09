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

### WordPress / Gutenberg (`src/pictova/publishers/`)

**Status: production-tested**

Uploads each image to the WordPress media library via REST API, then inserts a
Gutenberg image block at the correct position in the article content.

Required environment variables:
```
WORDPRESS_URL=https://yoursite.com
WORDPRESS_USERNAME=your_user
WORDPRESS_APP_PASSWORD=your_app_password
```

WordPress is one adapter among many. Nothing in the core engine is specific to WordPress.

### Ghost (`src/pictova/publishers/`)

**Status: stub / reference implementation**

Demonstrates the expected interface for a Ghost adapter. Not production-tested.

### Strapi (`src/pictova/publishers/`)

**Status: stub / reference implementation**

Demonstrates the expected interface for a Strapi adapter. Not production-tested.

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
