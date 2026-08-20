# Release status

This page is the canonical public explanation of which Pictovap version is
safe to install and which version is still being developed.

## Stable published release

- Version: **0.12.0**
- PyPI: <https://pypi.org/project/pictovap/0.12.0/>
- GitHub release: <https://github.com/yoldaolmak/Pictovap/releases/tag/v0.12.0>
- Tag: `v0.12.0`

Install the stable release with:

```bash
python -m pip install --upgrade pictovap
```

The unpinned command above resolves the latest package published to PyPI. It
does not install the unreleased contents of the repository `main` branch.

## Development version on `main`

- Version declared by the checkout: **0.13.0**
- Publication state: **unreleased**
- Changelog: [0.13.0 development entries](../CHANGELOG.md)
- Prepared release notes: [v0.13.0](release-notes/v0.13.0.md)

The `main` branch may contain changes that are not present in the stable PyPI
package. Do not describe `0.13.0` as published until its tag, GitHub release,
and PyPI upload all exist and have been checked against one another.

## Release identity rule

For every published version, these four identifiers must agree:

1. `pyproject.toml` and `src/pictovap/__init__.py`
2. the Git tag (`vX.Y.Z`)
3. the GitHub release attached to that tag
4. the PyPI distribution version

The repository may prepare the next version on `main`, but its documentation
must label that version as unreleased until the final three public artifacts
exist.
