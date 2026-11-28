# ActoVisio Framework

[![PyPI](https://img.shields.io/pypi/v/pictovap.svg)](https://pypi.org/project/pictovap/)
[![CI](https://github.com/yoldaolmak/ActoVisio-Framework/actions/workflows/ci.yml/badge.svg)](https://github.com/yoldaolmak/ActoVisio-Framework/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**ActoVisio Framework** is an open-source, CLI-first visual-decision framework for
publishers. Given an article and image candidates, it explains which images
fit each section, why, what source/license evidence is known, and how a CMS
could place them. The output is reviewable; it is not publication approval.

Formerly Pictovap Framework, it retains the `pictovap` Python package, CLI,
and existing public contracts. The same public repository was renamed to
`ActoVisio-Framework` on 28 November 2026. This identity change does not
alter MIT rights or require the separate enterprise application.

ActoVisio Framework is CMS-independent and does not require a hosted service.

## What works

```text
Article → Visual Brief → Candidates → Fit Score + intent proof
        → Global selection → Provenance + CMS placement
        → Visual Plan → explain / audit / diff → Decision Pack
```

- Deterministic article-aware selection with reasons for rejected and chosen
  candidates, slot coverage, and explicit source-attempt evidence.
- Portable provenance, metadata, CMS placement instructions, and a
  side-effect-free Decision Pack builder, validator, and review transition.
- Local and remote image-source adapters; WordPress as the broadest CMS
  adapter, with reference Ghost and Strapi implementations.
- A credential-free demo, a golden corpus benchmark, external-adapter
  contracts, and English/Turkish deterministic metadata templates.

Framework owns visual decisions for **one article**. ActoVisio is the
proprietary enterprise platform built on the Framework in the approved target
architecture. It owns site-wide visual inventory, lineage, governance,
execution and independent verification. Framework is independently usable
under MIT. See the [Framework/Product boundary](docs/architecture/core-product-boundary.md).

## Get started

Requires Python 3.10+. The published stable release is **0.13.0**. See
[Release Status](docs/release-status.md) for package and source identity.

Install the published package:

```bash
python -m pip install pictovap
pictovap demo
```

Or use a development checkout:

```bash
git clone https://github.com/yoldaolmak/ActoVisio-Framework.git
cd ActoVisio-Framework
python -m pip install -e ".[test]"
pictovap demo
```

The demo uses deterministic local data: no credentials or network access.
For your own Markdown article, start with the
[sample publisher profile](examples/profiles/sample-publisher.yaml):

```bash
pictovap plan \
  --article article.md \
  --profile examples/profiles/sample-publisher.yaml \
  --output plan.json \
  --report editor-report.md

pictovap validate --plan plan.json
pictovap explain --plan plan.json --format markdown
pictovap audit --plan plan.json --format markdown
```

The JSON plan is a machine-readable proposal. The report and explanation
provide a reviewable editor view. Use `pictovap diff` to compare existing
plans without contacting providers or the CMS:

```bash
pictovap diff --before plan-old.json --after plan.json --format markdown
pictovap benchmark --corpus tests/corpus
```

A Python integration can build a Decision Pack from a validated plan:

```python
from pictovap import build_decision_pack, validate_decision_pack

pack = build_decision_pack(plan)
assert validate_decision_pack(pack)["status"] == "passed"
```

To complete an editor review without hand-editing the Decision Pack JSON,
run the interactive, offline command on the **development checkout**:

```bash
pictovap review --plan plan.json --actor editor@example.test \
  --output reviewed-pack.json --preview review-preview.md

pictovap review-preview --plan plan.json \
  --reviewed reviewed-pack.json --format markdown
```

Review proposals and eligible alternatives offline with the CLI or the
[Gutenberg reference sidebar](examples/wordpress-review-sidebar/README.md).
See [Decision Pack](docs/concepts/decision-pack.md) for review and import
semantics. Review never updates a CMS post.

## Sources, CMS, and rights

Built-in image sources include local files, Unsplash, DepositPhotos,
Openverse, and Pexels. Live providers may require credentials; unavailable
sources must be recorded as **not evaluable**, not silently reported as
zero search results. Search results do not establish purchased image rights.
For example, a Depositphotos preview is not a licensed asset.

WordPress supports the broadest in-tree placement behavior. Ghost and
Strapi are reference adapters with documented gaps. A plan, dry run, or
reviewed pack does not authorize or prove a CMS update. Check rights,
deployment credentials, and the actual CMS result independently.

## Documentation and contributing

- [Documentation portal](docs/README.md) — choose Evaluate, Use, or Extend
- [Quickstart](docs/quickstart.md) and [WordPress setup](docs/guides/wordpress-setup.md)
- [Architecture](docs/ARCHITECTURE.md) and [API Stability](API_STABILITY.md)
- [Adapter contracts](docs/adapters/overview.md) and [plugin authoring](docs/contributing/plugins.md)
- [Developer guide](docs/DEVELOPER.md) and [contributing](CONTRIBUTING.md)

For contribution opportunities and safe feedback, see [Contributing](CONTRIBUTING.md).

ActoVisio Framework is MIT licensed ([LICENSE](LICENSE)). It has working offline
tests and adapters and a reference Gutenberg review sidebar, but does not
claim a production-ready graphical editor, broad adoption, licensed rights
from search alone, or verified publishing outcomes.
