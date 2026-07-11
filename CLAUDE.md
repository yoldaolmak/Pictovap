# Pictovap — Agent Handoff / Project Memory

This file is a handoff from a Cowork session to whatever picks up next
(Claude Code, another Cowork session, a human). Read this before touching
the repo. It captures state and hard-won lessons that aren't visible from
the code alone.

## Standing rules (non-negotiable, established with the maintainer)

- **Language:** all code, comments, docs, commit messages, and CI output
  must be in English. This framework is meant to be genuinely
  multi-language for generated content — never hardcode Turkish/English
  assumptions into the pipeline itself.
- **Pictova vs. Pictovap:** the legacy personal project ("Pictova") and this
  repo ("Pictovap") are different products. There is no backward-compatibility
  obligation to the legacy one. If you find personal-machine assumptions,
  hardcoded personal paths, or dead personal-infra code, that's a bug to fix,
  not a feature to preserve. See the "personal infra" lesson below — this has
  happened more than once and slipped past a "completed" cleanup task before.
- **Documentation quality bar:** premium, pain/solution-framed, honest —
  not marketing fluff. This was stated emphatically by the maintainer; don't
  re-litigate it, just hold the bar.
- **Claude-for-OSS:** the maintainer's stated goal is genuine eligibility —
  real PyPI downloads/dependents, real external contributors, real merged
  PRs. Never fabricate adoption signals (stars, downloads, contributors,
  fake engagement). The actual eligibility criteria are metric-based, not
  code-quality-based — see `https://claude.com/contact-sales/claude-for-oss`
  if this needs re-verifying. The legitimate levers are: make the repo easy
  to contribute to (accurate `good-first-issues.md`/`starter-issues.md`,
  working CI, clear adapter contracts) and get the package genuinely
  published and discoverable.

## Critical process lessons from the last session

1. **`pip install -e .` masks real packaging bugs.** All-session testing via
   editable install passed 150+/150+ tests, but a genuine `pip install
   ".[test]"` in a clean venv (matching exactly what CI and PyPI users
   actually do) failed immediately. Found and fixed three real bugs this way:
   a missing `src/pictova/services/__init__.py` (silently excluded a whole
   module from the built package), a demo sample-article path that only
   existed in a source checkout (crashed for every real end user), and an
   output-file path that landed inside site-packages internals for a real
   install. **Before trusting any packaging/release state, verify with a
   fresh venv doing a real `pip install .[test]` AND a wheel built via
   `python -m build` installed into a second, fully separate venv from a
   directory with no repo present at all.** That second step is the only
   thing that reliably catches this class of bug.
2. **Never test credential-handling code paths with raw ad-hoc scripts
   against the real `.env` file.** `load_project_env()` reads real secrets
   from disk via `os.environ.setdefault()`. A raw script cleared env vars
   then re-triggered a fresh load, printing real WordPress credentials into
   tool output once this session — caught, disclosed, no repo/git exposure,
   but avoidable. Use `pytest`'s `monkeypatch.setenv`/`monkeypatch.delenv`
   for any credential-path test, never a bare script.
3. **Trust but verify subagent work, always.** Delegating focused fixes to
   `sonnet`/`haiku` subagents works well for well-scoped tasks, but two real
   issues slipped through in agent-reported "done and verified" work this
   session: a commit message corrupted with stray shell output, and a fix
   that introduced a small behavioral regression (unconditional report
   generation) despite the agent's own tests passing. Always read the actual
   diff and independently re-run the verification bar yourself before
   considering delegated work final.

## Current release state (as of last session, 2026-07-10/11)

- Version bumped to **0.2.1** in `pyproject.toml`. The `v0.2.0` git tag
  already exists on GitHub and its `.github/workflows/publish.yml` run
  already failed at the test step (before the three packaging bugs above
  were found and fixed) — nothing was published to PyPI under that tag, but
  don't reuse/move it. Tag `v0.2.1` instead.
- **Pending action (maintainer's own machine, not doable from an agent
  sandbox — no push credentials there):**
  ```
  git push origin main
  git tag v0.2.1
  git push origin v0.2.1
  ```
  This triggers `.github/workflows/publish.yml`: runs `pytest tests/unit/`,
  then builds and publishes to PyPI via OIDC trusted-publisher (no token
  secret needed). PyPI trusted publisher, the GitHub `release` environment,
  and 2FA were already confirmed configured by the maintainer.
- After it runs, verify at `https://pypi.org/project/pictovap/` and via the
  GitHub Actions run status before considering the release done.

## Open task queue (see full history in prior session transcripts if needed)

- Write adapter developer docs + a runnable `examples/adapters/` directory
  (the conceptual contract is already documented in
  `docs/contributing/adapters.md`, but there's no runnable skeleton code yet).
- Rename the importable package `pictova` → `pictovap` (mechanical but
  wide-reaching; currently both names work as console scripts and the
  duality is intentional/tracked, see `docs/architecture/naming.md`).
- Final verification pass once the above land: `flake8 src/
  --max-line-length=120`, `pytest tests/unit -q`, demo smoke test, docs link
  check.

## Where things live

- Adapter contracts: `src/pictova/core/adapters.py` (formal `Protocol`s).
- Image source adapters (implemented): Local, Unsplash, DepositPhotos,
  Openverse (no key needed), Pexels. Open for contribution: Pixabay,
  Wikimedia Commons — see `docs/contributing/good-first-issues.md`.
- CMS adapters: WordPress (`services/wordpress.py`, production-hardened),
  Ghost/Strapi (`publishers/`, real reference implementations with
  documented gaps).
- Docs entry point: `docs/README.md`. Architecture: `docs/ARCHITECTURE.md`
  and `docs/adapters/overview.md`.
- CI: `.github/workflows/ci.yml` (lint + test on push), `publish.yml`
  (build + PyPI publish on `v*` tag push).
