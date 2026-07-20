# Contributing to pictovap-pixabay

This package is a standalone Pictovap provider plugin. Keep the
implementation boundary small: the adapter converts provider results into
Pictovap candidates, and Pictovap owns planning and publishing.

## First successful loop

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
pytest
pictovap plugins --kind provider
pictovap doctor --provider pixabay
```

## Definition of done

- Keep credentials in environment variables or explicit constructor arguments.
- Mock provider HTTP calls in tests.
- Validate the public boundary with `assert_image_source_contract`.
- Run `pictovap plan` with this provider before releasing.
- Document license and attribution behavior for returned images.
