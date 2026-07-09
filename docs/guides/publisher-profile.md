# Publisher Profile

A publisher profile defines how Pictovap behaves for a specific publication. It acts as the configuration layer for output rules, ensuring consistency across automated visual finishing.

## Configuration Fields

Profiles are defined in YAML format.

### Required Fields
- `id`: A unique string identifier for the profile.
- `brand`: The human-readable name of the publication.
- `language`: The default language code (e.g., `en`, `tr`) used for alt text and captions if not explicitly overridden by the article context.
- `cms_type`: The target CMS platform (e.g., `wordpress`, `ghost`).

### Optional Fields (Rules)
- `output_rules`: A list of rules dictating final image transformations (e.g., max dimensions, quality settings).
- `filename_rules`: Guidelines for formatting generated image filenames (e.g., prefixing with the brand name or using specific separators).
- `alt_text_rules`: Constraints for alt text generation (e.g., max length, tone).
- `caption_rules`: Constraints for editorial captions.
- `image_source_adapters`: A prioritized list of image sources to use (e.g., `['local', 'unsplash']`).

## Example Profile

```yaml
id: "sample-publisher"
brand: "Sample Magazine"
language: "en"
cms_type: "wordpress"

output_rules:
  format: "webp"
  max_width: 1200
  quality: 80

filename_rules:
  prefix: "sample-mag-"
  separator: "-"

alt_text_rules:
  max_length: 125
  descriptive: true

image_source_adapters:
  - "local"
```
