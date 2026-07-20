# Framework Guide

This guide is for developers integrating Pictovap with their own image source,
CMS, or review workflow. The core stays CMS-neutral; integrations live at the
public adapter boundary.

## 1. Create a Publisher Profile

Start with a versioned YAML profile. It states publisher defaults without
putting site-specific behavior in Pictovap core.

```yaml
schema_version: 1
profile_id: harbor-journal
brand_name: Harbor Journal
cms_type: custom-cms
language: en
image_sources:
  - harbor-images
output_rules:
  format: webp
forbidden_patterns:
  - unrelated stock imagery
```

## 2. Implement an Image Source Adapter

An image source returns JSON-safe candidate records. Keep credentials in the
constructor or environment; construction itself must not make a request.

```python
class HarborImageSource:
    def search_candidates(self, query: str, count: int) -> list[dict]:
        return [{
            "id": "harbor-1",
            "filename": "harbor.jpg",
            "provider": "harbor-images",
            "source_type": "url",
            "local_path": None,
            "source_url": "https://images.example.test/harbor.jpg",
            "license": "cc0",
            "attribution": None,
            "keywords": ["harbor"],
            "width": 1600,
            "height": 1000,
        }][:count]
```

For a CMS adapter, implement `place(placement)` and return `placed`,
`failed`, and `warnings`. For a report renderer, implement `render(plan)` and
return a non-empty string.

## 3. Run the Contract Test

```python
from pictovap.testing import assert_image_source_contract

adapter = HarborImageSource()
assert_image_source_contract(adapter, query="harbor", count=3)
```

This validates the protocol, candidate fields, JSON safety, and requested
candidate limit. Add the equivalent helper to your plugin's own test suite.

## 4. Call the Planning API

```python
from pictovap import create_visual_plan

plan = create_visual_plan(
    article="article.md",
    profile="harbor-journal.yaml",
    provider_adapter=HarborImageSource(),
    provider_name="harbor-images",
    output="plan.json",
)
```

The returned plan is the reviewable boundary between selection and publishing.
Use `CMSPlacement` from the plan only after an editor has approved it.

## 5. Generate an Editor Report

```bash
pictovap report --plan plan.json --output review.md
```

For a separate renderer package, register an entry point under
`pictovap.report_renderers`, then run:

```bash
pictovap report --plan plan.json --output review.html --renderer your-renderer
pictovap adapter check --kind renderer --name your-renderer
```

The complete [external renderer package example](../examples/external-renderer-package/README.md)
shows package metadata, discovery, contract testing, and CLI execution.

## Before You Publish an Adapter

1. Keep adapter imports and construction credential-free.
2. Mock network and CMS writes in your tests.
3. Run `pictovap adapter check` and preserve its JSON report in CI output.
4. Review [API Stability Policy](../API_STABILITY.md) and depend only on
   stable contracts.
