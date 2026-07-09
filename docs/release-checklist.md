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

## Release Process

- [ ] Tag created only after maintainer approval (`git tag -a v0.x.y -m "..."`)
- [ ] GitHub release published manually with release notes

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
- [ ] Open planned GitHub issues from `docs/github-issue-plan.md`
- [ ] Notify any external testers (see `docs/external-tester-note.md`)
