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

## Development candidate (not published)

- Version: **0.14.0**
- Canonical distribution and CLI: `actovisio-framework`
- Python namespace: `actovisio_framework`
- Legacy compatibility distribution: `pictovap` 0.14.0, separate wheel

The public name and Trusted Publishing authorization must be confirmed before
publication. Both wheels need clean-environment verification, including upgrade
from 0.13.0 and historical Decision Pack replay. Publish the canonical wheel first;
the legacy distribution is never published by the canonical release job. Product
#153 remains pinned to the existing released 0.13.0 until its independent gate.

## Release identity

The declared package version, immutable Git tag, GitHub Release, and PyPI
distribution must agree. Development changes after a release are not part of
that published distribution.

A reviewed change to `release-request.json` initiates the protected release
workflow. The workflow validates version identity, tests the package, verifies
a clean wheel, publishes to PyPI, and creates the matching GitHub Release.
Tag-triggered releases retain the same identity and publication checks.
