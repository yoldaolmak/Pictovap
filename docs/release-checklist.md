# Release Checklist

Follow this checklist before publishing a new Pictovap release.

## Pre-Release

- [ ] All tests pass: `source .venv/bin/activate && pytest`
- [ ] Local demo runs successfully: `make demo`
- [ ] Demo output is valid and complete
- [ ] No credential requirements for demo path
- [ ] Version bumped in `pyproject.toml`
- [ ] Version bumped in `src/pictova/__init__.py`
- [ ] `CHANGELOG.md` updated with release notes
- [ ] All documentation links are valid
- [ ] README accurately describes current functionality

## Build

- [ ] Package builds cleanly: `python -m build`
- [ ] Package installs in a fresh venv
- [ ] CLI entry point works after install: `pictova --help`

## Release

- [ ] Create a git tag: `git tag vX.Y.Z`
- [ ] Push tag: `git push origin vX.Y.Z`
- [ ] Create GitHub release with changelog excerpt
- [ ] Publish to PyPI (when authorized): `twine upload dist/*`

## Post-Release

- [ ] Verify PyPI page shows correct metadata
- [ ] Test install from PyPI in a clean environment
