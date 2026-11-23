# Pictovap

[![PyPI](https://img.shields.io/pypi/v/pictovap.svg)](https://pypi.org/project/pictovap/)
[![CI](https://github.com/yoldaolmak/Pictovap/actions/workflows/ci.yml/badge.svg)](https://github.com/yoldaolmak/Pictovap/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Pictovap Core** is an open-source, CLI-first visual-decision framework for
publishers. Given an article and image candidates, it explains which images
fit each section, why, what source/license evidence is known, and how a CMS
could place them. The output is reviewable; it is not publication approval.

Pictovap grew out of an editorial workflow at
[Yoldaolmak.com](https://yoldaolmak.com). See the
[case study](docs/case-studies/yoldaolmak.md) for the original problem and
its limits. Pictovap is not a stock-photo library, generic AI image
generator, DAM, or WordPress-only tool.

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

Core knows visual decisions for **one article**. A separate enterprise
Product owns site-wide visual inventory, permissions, execution lifecycle,
and independent verification. Read the
[Product Contract](docs/architecture/core-product-boundary.md) for that split.

## Get started

Requires Python 3.10+. The published stable release is **0.12.0**;
`main` is the unreleased **0.13.0** development line. Check
[Release Status](docs/release-status.md) before comparing them.

Install the published package:

```bash
python -m pip install pictovap
pictovap demo
```

Or use a development checkout:

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap
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

For each slot, accept the proposal, reject the image, or select an eligible
alternative. New plans include source-backed alternative evidence: the
Gutenberg reference sidebar offers direct one-click choices with no
replacement JSON preparation. Older plans can still use an existing atomic
`candidate_id`/`provenance`/`placement` record. Core rejects a changed
or invented replacement in new packs, and always keeps
`application.status=not_applied`.

A Gutenberg [reference review sidebar](examples/wordpress-review-sidebar/README.md)
now supports offline per-post decisions, one-click source-evidenced
alternatives and local image comparisons. Editors explicitly choose
local image files; no remote image URL is loaded, and image bytes are not
uploaded or exported. The sidebar exports only an unverified local draft;
Core verifies the original pack fingerprint and decisions with
`pictovap review-import` before producing a reviewed pack. It never
updates a WordPress post. This reference has not passed a real editor trial. See [Decision Pack](docs/concepts/decision-pack.md)
and [Roadmap](docs/ROADMAP.md).

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

Small first contributions: [realistic article fixture (#65)](https://github.com/yoldaolmak/Pictovap/issues/65)
or [editor-report terminology (#66)](https://github.com/yoldaolmak/Pictovap/issues/66).
If you test a real, non-sensitive article, use
[publisher feedback](https://github.com/yoldaolmak/Pictovap/issues/new?template=external_validation.md);
do not attach credentials or private article data.

Pictovap is MIT licensed ([LICENSE](LICENSE)). It has working offline
tests and adapters and a reference Gutenberg review sidebar, but does not
claim a production-ready graphical editor, broad adoption, licensed rights
from search alone, or verified publishing outcomes.
