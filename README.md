# Pictovap

[![CI](https://github.com/yoldaolmak/Pictovap/actions/workflows/ci.yml/badge.svg)](https://github.com/yoldaolmak/Pictovap/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Pictovap is an open-source visual finishing engine for content publishers.**
It turns a finished article into a visually complete, rights-aware,
publish-ready CMS page — and shows its work at every step.

## The Problem

Every publisher runs the same manual routine before an article can go live:
find images that actually fit the section they're going into, check whether
the license permits the intended use, resize and convert them to the site's
format, write alt text and a caption for each one, and place them at the
right point in the CMS. None of this is hard, individually. It is, however,
*repetitive*, *easy to get wrong under deadline pressure*, and it *scales
linearly with how much a publisher writes*. Skipped alt text quietly erodes
accessibility and SEO. Untracked image provenance is a license or attribution
problem waiting to surface later, when it's expensive to fix. None of this
shows up in a style guide — it shows up as an hour of an editor's afternoon,
per article, forever.

Point solutions exist for pieces of this: stock photo plugins, DAM systems,
generic AI image generators. What's largely missing is the connective layer
— something that reads what the article actually needs, evaluates candidates
against that need with a visible, auditable reason for every accept and
reject, and hands a CMS a placement plan it can execute without a human
re-deriving the same context from scratch.

## The Solution

Pictovap is that connective layer, built as an open, adapter-based pipeline
rather than a closed SaaS product:

```
Article Input → Visual Brief → Candidate Images → Fit Score
              → Provenance Pack → CMS Placement → Editor Report
```

- **Visual Brief** — a structured read of what imagery the article actually
  needs, derived from its heading structure and content, not from a generic
  "insert 3 images" rule.
- **Fit Score** — every candidate is scored against the brief with a
  transparent, deterministic reason attached (`selected`, `rejected`, or
  `needs_review`, plus why). No black-box relevance number.
- **Provenance Pack** — a persistent audit trail for every selected image:
  source, license status, attribution, a content hash, and the exact
  processing actions applied. This is what makes "where did this image come
  from and are we allowed to use it" answerable six months later.
- **CMS Placement** — a CMS-agnostic plan describing where and how each image
  should be placed, independent of whether the destination is WordPress,
  Ghost, Strapi, or something a contributor writes an adapter for tomorrow.
- **Editor Report** — a human-readable Markdown review surface, so an editor
  signs off on a report, not raw JSON, before anything reaches production.

What makes this radical isn't any single stage — it's that the whole pipeline
is a public, inspectable contract instead of a hosted black box, and that it
is honest about its own workings by default: the credential-free demo below
runs the entire pipeline end-to-end, with zero API keys and zero network
calls, so you can read exactly what it does before you ever hand it a real
site.

Pictovap is not a stock photo search tool, a DAM, a generic AI image
generator, or a WordPress-only plugin. It has no graphical interface yet — it
is a CLI-first, adapter-based core, with the editor report as the intended
human review surface and CMS adapters as the machine-facing execution layer.

## Quickstart

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Run the credential-free demo:

```bash
pictovap demo
```

```text
  Brief:      4 slots from 3 sections
  Evaluated:  5 candidates
  Selected:   3 images
  Rejected:   4 candidates
  Placements: 3 instructions
```

No `.env` file, no API keys, no network calls — every candidate and score
above comes from deterministic mock data, on purpose. This is the demo's
guarantee, not just its default state.

## Try Your Own Article

```bash
pictovap plan \
  --article path/to/your/article.md \
  --profile examples/profiles/sample-publisher.yaml \
  --output my-plan.json \
  --report my-report.md
```

`my-plan.json` is the canonical, machine-readable artifact for adapters and
automation. `my-report.md` is the same plan, rendered for a human editor to
review before anything gets published.

## Adapters

Pictovap connects to the outside world only through adapters — the core
pipeline has no hardcoded dependency on any specific image provider or CMS.

**Image sources:** local folder, Unsplash, DepositPhotos are implemented;
Openverse is planned. See [Image Source Adapters](docs/adapters/image-sources.md).

**CMS placement:** WordPress (production-tested), Ghost and Strapi (reference
implementations, real but with documented limitations). See
[CMS Adapters](docs/adapters/cms-adapters.md).

Every adapter degrades gracefully when unconfigured — a missing API key
produces an empty result, not a crash, so a partially configured profile
still runs. Writing a new adapter means implementing one method
(`search_candidates` or `place`) against a documented `Protocol`; see the
[Adapter Overview](docs/adapters/overview.md).

## Multi-Language by Design

Pictovap's own code, comments, and documentation are English. What it
*generates* — alt text, captions, titles — is not tied to any one language.
Article language is detected automatically (or set explicitly via the
publisher profile), and generated metadata follows it: a Turkish article
gets Turkish alt text, a French one gets French, and so on. This isn't a
localization afterthought bolted onto an English-only tool; it's a parameter
of the pipeline from the start.

## Current Status and Limitations

Pictovap is early open-source infrastructure. It has a genuinely
credential-free local demo, documented core primitives, a real test suite,
and a working adapter model — it does not yet claim broad ecosystem adoption
or a large external contributor base.

Specifically:

- Only the WordPress CMS adapter is production-hardened; Ghost and Strapi are
  real, tested reference implementations with documented gaps (see
  [CMS Adapters](docs/adapters/cms-adapters.md)).
- The credential-free demo always uses deterministic mock candidates by
  design, regardless of what's configured in `.env` — `pictovap plan` is
  where real, credentialed sources are used.
- Deterministic structural extraction (the rule-based, non-AI language and
  section detection) is reliable for English and Turkish; other languages
  are untested.

## Compatibility Note

Product name: Pictovap. The Python package, import name, and console-script
entry point may remain `pictova` for backward compatibility — see
[Brand & Naming](docs/architecture/naming.md).

## Contributing

See the [Documentation Portal](docs/README.md) for architecture, concepts,
and adapter-writing guides, and [DEVELOPER.md](docs/DEVELOPER.md) for the
contribution workflow. Pull requests that add a new image source or CMS
adapter, improve test coverage, or fix documentation are all welcome.

## License

MIT — see [LICENSE](LICENSE).
