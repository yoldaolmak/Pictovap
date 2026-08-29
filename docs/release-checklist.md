# Release Checklist

Follow this final pre-release sequence before publishing a new Pictovap release.

## Pre-Release Verification

- [ ] Clean git status (`git status` shows no unexpected changes)
- [ ] All unit tests pass (`pytest tests/unit -v`)
- [ ] Demo runs successfully (`make demo`)
- [ ] Docs link check passes (`make check-docs`)
- [ ] Public-language guard passes (`pytest tests/unit/test_public_language.py -v`)
- [ ] Package builds without errors (`python -m build`)
- [ ] CHANGELOG.md updated with release date and all sections
- [ ] Release notes prepared in `docs/release-notes/`
- [ ] No secrets or credentials in committed files
- [ ] No fake adoption claims (stars, forks, downloads, contributors)
- [ ] CI pipeline is green on main branch
- [ ] Stable version, Git tag, GitHub release, and PyPI version are identical
- [ ] The next development version is clearly labeled unreleased in README and release docs

## Final Manual Release

Before tagging:

* clean git status
* tests pass
* demo runs
* docs links pass
* public-language guard passes
* package builds
* CI is green on main
* release notes ready
* no secrets
* no fake adoption claims

Manual release steps:

```bash
git tag -a vX.Y.Z -m "Pictovap vX.Y.Z"
git push origin vX.Y.Z
gh release create vX.Y.Z --verify-tag \
  --title "Pictovap X.Y.Z" \
  --notes-file docs/release-notes/vX.Y.Z.md
```

Use the same version in `pyproject.toml`, `src/pictovap/__init__.py`, the tag,
the GitHub release, and the PyPI artifact. Do not create a release object for
a tag whose package version or release notes disagree with it.

## Package Build Verification

Verify that the wheel and source distribution build correctly without uploading:

```bash
python -m pip install --upgrade build
python -m build
```

Inspect the output in `dist/` to confirm the package name, version, and included files are correct.

## Post-Release

- [ ] Verify the tag is visible on GitHub
- [ ] Verify the release notes render correctly
- [ ] Confirm planned issue links point to live GitHub issues; do not reopen the historical drafts in `docs/github-issue-plan.md`
- [ ] Notify any external testers (see `docs/external-tester-message.md`)
