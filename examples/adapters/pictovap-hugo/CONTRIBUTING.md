# Contributing to pictovap-hugo

This package is a standalone Pictovap CMS plugin example. Keep the boundary
small: the adapter receives a typed `CMSPlacement`, writes Hugo-compatible
shortcodes into Markdown content, and returns `placed`, `failed`, and
`warnings`.

## First Successful Loop

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
pytest
pictovap plugins --kind cms
pictovap adapter check --kind cms --name hugo
```

## Definition of Done

- Keep all writes inside the configured Hugo content directory.
- Make placement idempotent with stable Pictovap markers.
- Preserve alt text and captions in the generated shortcode.
- Validate the public boundary with `assert_cms_adapter_contract`.
- Run `pictovap publish --dry-run` before enabling real writes in a workflow.
