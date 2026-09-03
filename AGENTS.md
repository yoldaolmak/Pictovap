# Working in this repository

Instructions for any agent or contributor making changes here. This file is
about how to work, not what to build; the roadmap lives in
[docs/ROADMAP.md](docs/ROADMAP.md) and open work in the issue tracker.

## Standing rules

- **English only.** Code, comments, documentation, commit messages, and CI
  output are English. Pictovap generates content in multiple languages; never
  hardcode a language assumption into the pipeline itself.
- **Documentation is pain/solution-framed and honest.** No marketing language,
  no capability stated above what the repository can demonstrate. If a claim
  needs a qualifier, write the qualifier.
- **Never fabricate adoption signals.** Stars, downloads, dependents,
  contributors, and testimonials are reported as they are or not at all.
- **Pictova is not Pictovap.** The legacy personal project shares a root name
  and nothing else. There is no backward-compatibility obligation to it. A
  hardcoded personal path or leftover personal-infrastructure code is a bug to
  remove, not a behaviour to preserve.

## Verification bar

- **Do not trust an editable install for packaging state.** `pip install -e .`
  hides real packaging defects — a missing `__init__.py` that silently drops a
  module from the wheel, a data file that exists only in a source checkout, an
  output path that resolves inside `site-packages`. Before trusting any
  packaging or release state, build a wheel with `python -m build` and install
  it into a clean virtualenv, then run it from a directory with no repository
  present.
- **Never exercise credential paths with ad-hoc scripts.** `load_project_env()`
  reads real secrets from `.env` into the process environment. Use pytest's
  `monkeypatch.setenv` / `monkeypatch.delenv` for any test that touches a
  credential path, never a bare script against the real file.
- **Read the diff of delegated work.** A subagent reporting "done and verified"
  is not verification. Re-run the gates yourself and read the actual change
  before treating it as final.

## Architectural invariants

- **The planning engine is silent.** `engine/planner.py` prints nothing and
  writes no files. Anything a human reads on screen is rendered from the
  returned plan, so a terminal view can never disagree with the artifact.
- **`pictovap.api` is the only public planning API.** `pictovap.demo` is a
  runner for the credential-free example and owns no pipeline logic.
- **Degrading quietly is not degrading silently.** An adapter that cannot run
  produces an evidence record, not an empty result that reads as an
  observation. See `core/sources.py` and `runtime.sources` in a plan.
- **A plan never implies execution.** Producing, validating, or reviewing a plan
  says nothing about whether a CMS authorized, applied, published, or verified
  anything.

## Where things live

- Adapter contracts: `src/pictovap/core/adapters.py` (formal `Protocol`s).
- Planning engine: `src/pictovap/engine/planner.py` builds the plan,
  `engine/scoring.py` holds Fit Score, `engine/reporting.py` renders reports and
  writes artifacts. Public entry point: `src/pictovap/api.py`.
- Image source adapters: Local, Unsplash, DepositPhotos, Openverse (no key
  needed), Pexels, in `src/pictovap/providers/`. Open for contribution: Pixabay,
  Wikimedia Commons — see [docs/contributing/good-first-issues.md](docs/contributing/good-first-issues.md).
- CMS adapters: WordPress (`services/wordpress.py`, broadest in-tree placement
  behaviour), Ghost and Strapi (`publishers/`, reference implementations with
  documented gaps).
- Docs entry point: [docs/README.md](docs/README.md). Architecture:
  [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Public surface guarantees:
  [API_STABILITY.md](API_STABILITY.md).
- CI: `.github/workflows/ci.yml` (lint, typecheck, test), `publish.yml` (build
  and publish to PyPI on a `v*` tag).

## Gates before calling a change done

```bash
make contribution-check
```

That runs the contributor smoke test, flake8, pyright, the unit suite, the
documentation link check, and the security hygiene tests. Add
`make markdownlint` when documentation changed, and
`pictovap benchmark --corpus tests/corpus` when planning behaviour changed.
