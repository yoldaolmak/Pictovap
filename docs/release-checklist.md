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
git tag -a v0.2.0 -m "Pictovap v0.2.0"
git push origin v0.2.0
```

Then create GitHub Release manually using:

`docs/release-notes/github-release-v0.2.0.md`

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
