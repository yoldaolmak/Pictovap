# Writing Adapters

This guide covers how to write new adapters for Pictovap — either image source
adapters (new providers) or CMS adapters (new publishing targets).

## Before You Start

Read the [Adapter Architecture Overview](../adapters/overview.md) to understand
the two adapter types and where they live in the codebase.

**Prefer starting from running code?** [`examples/adapters/`](../../examples/adapters/README.md)
contains a runnable skeleton for each adapter type — both execute the real
contracts with zero credentials:

```bash
python examples/adapters/custom_image_source.py
python examples/adapters/custom_cms_adapter.py
```

## Image Source Adapters

Image source adapters add new ways to supply candidate images to the pipeline.

### File Location

```
src/pictovap/providers/<your_source_name>.py
```

### Required Output Shape

Your adapter must return a list of dicts. Each dict must contain at minimum:

```python
{
    "id": str,
    "filename": str,
    "provider": str,       # Your adapter's name
    "source_type": str,    # "local", "api", or "url"
    "local_path": str,     # None if not local
    "source_url": str,     # None if local-only
    "license": str,
    "attribution": str,    # None if no attribution required
    "keywords": list[str],
    "width": int,
    "height": int,
}
```

### Unit Test Requirements

Every adapter must have a test that:
- Mocks any external HTTP call
- Asserts the returned list contains dicts with the required fields
- Tests at least one error case (empty result, API failure)

### Checklist

- [ ] Adapter file in `src/pictovap/providers/`
- [ ] Credentials (if any) come from environment variables only
- [ ] `.env.example` updated with credential key names
- [ ] Unit tests with mocked HTTP
- [ ] Entry in `docs/adapters/image-sources.md`
- [ ] Example profile key in `examples/profiles/`

## CMS Adapters

CMS adapters consume the `CMSPlacement` plan and place images in a target CMS.

### File Location

```
src/pictovap/publishers/<your_cms_name>_adapter.py
```

### Required Interface

```python
from pictovap.core.primitives import CMSPlacement

class MyCMSAdapter:
    def __init__(self, profile):
        # Initialize with credentials from environment, not hardcoded
        ...

    def place(self, placement: CMSPlacement) -> dict:
        # Execute placement instructions
        # Return result dict
        return {
            "placed": [...],
            "failed": [...],
            "warnings": [...],
        }
```

### Unit Test Requirements

Every adapter must have a test that:
- Mocks all HTTP/API calls using `unittest.mock.patch`
- Asserts the placement result dict shape
- Tests at least one failure case

### Checklist

- [ ] Adapter file in `src/pictovap/publishers/`
- [ ] Credentials from environment only
- [ ] `.env.example` updated
- [ ] Unit tests with mocked HTTP
- [ ] Entry in `docs/adapters/cms-adapters.md`

## Credential Policy

No adapter may hardcode credentials. All credentials must be loaded from
environment variables. The local demo (`make demo`) must always be runnable
without any `.env` file. Tests must not require secrets.

## Submitting Your Adapter

Open a pull request. Reference the adapter type in the PR title:
- `feat(provider): add Openverse image source adapter`
- `feat(publisher): add Ghost CMS adapter`

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for the full contribution process.
