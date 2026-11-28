# Release Checklist

Follow this final pre-release sequence before publishing a new ActoVisio Framework release.

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

Release the canonical distribution through a separately reviewed PR changing
`release-request.json` on protected `main` to the candidate version. The
`publish.yml` workflow validates that exact version, runs tests, builds and
smoke tests the canonical wheel, publishes `actovisio-framework` to PyPI, and
only after a successful upload creates the matching tag and GitHub Release.
Never create or push a release tag as an alternate publication trigger.

Before opening that release-request PR, verify the PyPI project name is still
available and its pending Trusted Publisher matches this repository,
`publish.yml`, and the `release` environment. Verify the exact source commit,
full CI (including canonical/legacy wheel compatibility), independent review,
and release environment policy. The pending publisher does not reserve a name.

The separately built `pictovap` 0.14 compatibility distribution is **not**
uploaded by this canonical release workflow. Its publication requires a
separate acceptance and a matching trusted-publisher grant after the repository
rename. Until then, `pictovap==0.13.0` remains the published legacy version.
Do not imply that the compatibility wheel is available on PyPI before that
independent publication and clean-install verification.

Use the same version in `pyproject.toml`, `src/actovisio_framework/__init__.py`,
the generated tag, GitHub Release, and canonical PyPI artifact. Do not create
a Release object before the PyPI upload succeeds.

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
