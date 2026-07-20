# Development Assistants

This file gives maintainers and development assistants the repository-level
rules needed to make safe, reviewable changes.

## Product boundary

Pictovap is an open-source visual-finishing framework for content publishers.
It turns a Markdown or CMS article into a reviewable visual plan, then leaves
publishing as an explicit adapter operation. Keep the framework CMS-neutral:
WordPress and Gutenberg are important integrations, not the product boundary.

## Public contribution standard

- Write code, documentation, commit messages, pull requests, and issue
  responses in English.
- Keep public claims specific and verifiable. Do not imply adoption, support,
  compatibility, or outcomes that the repository cannot demonstrate.
- Preserve contributor attribution and review external changes on their actual
  behavior, tests, and security properties.
- Do not add personal-machine paths, local credentials, private URLs, or
  deployment assumptions to the repository.

## Extension boundaries

- Use the public contracts in `pictovap.core.adapters` for image sources, CMS
  adapters, and report renderers.
- Validate independently packaged adapters with `pictovap.testing` contract
  assertions and document their entry point.
- Treat Publisher Profile YAML as the versioned public contract documented in
  `docs/reference/publisher-profiles.md`.
- Keep credential-free demos deterministic and separate planning from CMS
  writes.

## Verification

Before a release or a behavior-changing merge, run the appropriate checks:

```bash
python -m pytest tests/unit -q
flake8 src --max-line-length=120
pyright
python -m build
```

For packaging changes, install the built wheel into a fresh virtual
environment outside the source checkout and run `python -m pictovap.demo`.
