# Pictovap

Open-source visual finishing for content publishers.

Pictovap turns unfinished articles into visually complete, rights-aware, publish-ready CMS pages.

## What is Pictovap?

It is the missing article-aware layer between written content and CMS publishing. It reads an article's structure, creates a visual brief, evaluates candidate images, records provenance, generates metadata, and produces CMS placement instructions.

Pictovap is **not** a stock photo search tool, a DAM, or a generic AI image generator.

## Why it exists

Independent publishers spend significant time on visual operations per article: finding images, checking licenses, resizing, writing alt text, and placing them in a CMS. This labor scales linearly with article volume. Pictovap automates this workflow so editors can focus on narrative quality.

## Quickstart

Get Pictovap running locally in under five minutes.

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Run the local credential-free demo:

```bash
make demo
```

## Demo Output

The demo runs the entire pipeline locally and outputs a summary of what it did:

```text
  Brief:      4 slots from 3 sections
  Evaluated:  5 candidates
  Selected:   3 images
  Rejected:   4 candidates
  Placements: 3 instructions
```

## Four Primitives

Pictovap operates on four core architectural primitives:

1. **Visual Brief:** Analyzes the article to determine exactly what imagery is needed.
2. **Fit Score:** Evaluates candidates deterministically against contextual, technical, and licensing criteria.
3. **Provenance Pack:** Maintains an audit trail tracking image origin, license, and processing actions.
4. **CMS Placement:** Produces a CMS-agnostic plan for where images should be injected.

## Adapter Model

Pictovap uses an adapter-based architecture:

- **Image Sources:** Local folder, Unsplash, DepositPhotos, Visual Memory DB.
- **CMS Placement:** WordPress (working), Ghost (stub), Strapi (stub).

## Current Limitations

- Core logic was recently extracted from production; some internal dict passing is still being migrated to strict primitives.
- The local demo uses mock assets rather than live API calls.
- Only the WordPress CMS adapter is production-hardened; others are reference implementations.

## Contributing

See the [Documentation Portal](docs/README.md) for full guides on architecture, concepts, and contribution.

## Compatibility Note

Product name: Pictovap.
Python package and legacy CLI may remain `pictova` for backward compatibility.
