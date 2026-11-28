# Release status

## Stable release

- Version: **0.13.0**
- Published: 2026-11-24
- PyPI: <https://pypi.org/project/pictovap/0.13.0/>
- GitHub: [v0.13.0](https://github.com/yoldaolmak/ActoVisio-Framework/releases/tag/v0.13.0)
- Tag: `v0.13.0`
- Commit: `aa353988f2927ffa90af4afc46ef435c31811c62`
- [Release notes](release-notes/v0.13.0.md)
- [Publication and clean-wheel acceptance](https://github.com/yoldaolmak/ActoVisio-Framework/actions/runs/45391982550)

```bash
python -m pip install pictovap==0.13.0
```

The published wheel and source distribution passed release checks. The tag
and GitHub Release bind the exact published source commit. Product integration
has its own acceptance gate.

## Release identity

The declared package version, immutable Git tag, GitHub Release, and PyPI
distribution must agree. Development changes after a release are not part of
that published distribution.

A reviewed change to `release-request.json` initiates the protected release
workflow. The workflow validates version identity, tests the package, verifies
a clean wheel, publishes to PyPI, and creates the matching GitHub Release.
Tag-triggered releases retain the same identity and publication checks.
