# Publisher Profiles

Publisher Profiles are configuration models that decouple the core engine from specific site hardcoding.

Instead of hardcoding rules for a specific site, Pictovap reads a `PublisherProfile` which defines:
- Language preferences
- Permitted image sources
- Output formatting rules (e.g., filename conventions)
- Alt text and caption templates
- Editorial constraints (e.g., forbidden patterns)

## Example Profile

```yaml
profile_id: example-blog
brand_name: Example Blog
cms_type: wordpress
language: en
image_sources:
  - local
  - unsplash
output_rules:
  format: webp
  max_width: 1200
```
