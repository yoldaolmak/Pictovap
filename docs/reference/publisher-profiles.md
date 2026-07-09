# Publisher Profiles Reference

A **Publisher Profile** is a configuration object that controls how Pictovap behaves
for a specific publisher. It decouples the core engine from site-specific hardcoding.

## Configuration Fields

| Field | Type | Description |
|---|---|---|
| `profile_id` | str | Unique identifier (e.g., `demo`, `sample-publisher`) |
| `brand_name` | str | Human-readable name used in logging and metadata prompts |
| `cms_type` | str | CMS target: `wordpress`, `ghost`, `strapi`, or `generic` |
| `language` | str | ISO language code for generated text (e.g., `en`, `tr`) |
| `language_mode` | str | Behavior for profile language: `fallback` (default) or `override` |
| `image_sources` | list[str] | Ordered list of adapter names to query (e.g., `["local", "unsplash"]`) |
| `output_rules` | dict | Image processing rules: `format`, `max_width`, `max_height`, `quality` |
| `filename_rules` | dict | Output filename rules: `prefix`, `case`, `separator` |
| `alt_text_rules` | dict | Alt text generation rules |
| `caption_rules` | dict | Caption generation rules |
| `editorial_preferences` | dict | Style guidance injected into metadata generation |
| `forbidden_patterns` | list[str] | Visual concepts to reject regardless of score |

## Built-in Default Profile

The built-in default profile is used by the local demo:

```python
from pictova.core.profile import PublisherProfile

profile = PublisherProfile.get_default_profile()
print(profile.profile_id)    # "demo"
print(profile.brand_name)    # "Demo Publisher"
print(profile.cms_type)      # "wordpress"
print(profile.image_sources) # ["local", "unsplash"]
```

## YAML Profiles

Publisher profiles can also be defined as YAML files. See the example:

```
examples/profiles/sample-publisher.yaml
```

YAML profiles are the recommended format for sharing publisher configurations
with the community. The Python `PublisherProfile` dataclass is the internal
representation; YAML is the external, human-editable format.

## Profile Example

```yaml
profile_id: my-blog
brand_name: My Blog

cms_type: ghost
language: en

image_sources:
  - local
  - unsplash

output_rules:
  format: webp
  max_width: "1200"
  quality: "85"

forbidden_patterns:
  - stock photo handshake
  - generic office backgrounds
```

## Using Profiles in Practice

Pass the profile to the engine when running a non-demo pipeline. In the current
version, profiles are loaded from the `PublisherProfile` dataclass or from a
YAML file. Full YAML loading from `src/pictova/profiles/` is planned.

## Compatibility Note

Product name: Pictovap.
Python package and legacy CLI may remain `pictova` for backward compatibility.
The `yoldaolmak` profile in `src/pictova/profiles/` is one example publisher
configuration, not the only supported site.
