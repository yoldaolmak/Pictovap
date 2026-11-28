# Release status

## Stable release

- Version: **0.14.0**
- Published: 2026-11-28
- Canonical distribution and CLI: `actovisio-framework`
- Python namespace: `actovisio_framework`
- PyPI: <https://pypi.org/project/actovisio-framework/0.14.0/>
- GitHub: [v0.14.0](https://github.com/yoldaolmak/ActoVisio-Framework/releases/tag/v0.14.0)
- Tag: `v0.14.0`
- Commit: `d722bb2cf6091881cebfa494704f6714db0ac174`
- [Release notes](release-notes/v0.14.0.md)
- [Publication and clean-wheel acceptance](https://github.com/yoldaolmak/ActoVisio-Framework/actions/runs/46138980635)

```bash
python -m pip install actovisio-framework==0.14.0
```

The published canonical wheel and source distribution passed SHA256,
clean-install, CLI, and Decision Pack verification. The immutable Git tag and
GitHub Release bind the exact published source commit. Product integration has
its own acceptance gate.

## Legacy compatibility (pictovap)

- Published legacy release: **0.13.0** (`2026-11-24`)
- PyPI: <https://pypi.org/project/pictovap/0.13.0/>
- GitHub: [v0.13.0](https://github.com/yoldaolmak/ActoVisio-Framework/releases/tag/v0.13.0)
- Commit: `aa353988f2927ffa90af4afc46ef435c31811c62`
- [Publication and clean-wheel acceptance](https://github.com/yoldaolmak/ActoVisio-Framework/actions/runs/45391982550)

`pictovap==0.13.0` remains the published legacy release on PyPI. The matching
`pictovap` 0.14.0 compatibility wheel is **not** published by the canonical
release workflow and requires its own trusted-publisher gate and clean-install
verification. Product #153 remains pinned to `pictovap==0.13.0` under its own
gate.

## Release identity

The declared package version, immutable Git tag, GitHub Release, and PyPI
distribution must agree. Development changes after a release are not part of
that published distribution.

A reviewed change to `release-request.json` initiates the protected release
workflow. The workflow validates version identity, tests the package, verifies
a clean wheel, publishes to PyPI, and creates the matching GitHub Release.
Release tags alone do not trigger publication. The matching legacy distribution
requires a separate publication gate and compatible trusted publisher after the
repository rename.
