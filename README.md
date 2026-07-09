# Pictovap

Open-source visual finishing for content publishers.

Pictovap turns unfinished articles into visually complete, rights-aware, publish-ready CMS pages.

It reads article structure, creates a visual brief, evaluates candidate images, records provenance, generates metadata, and produces CMS placement instructions.

Pictovap is not a stock photo search tool, a DAM, or a generic AI image generator. It is the missing article-aware layer between content and CMS publishing.

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

## How It Works: The Four Primitives

Pictovap operates on four core architectural primitives:

1. **Visual Brief:** Analyzes the article to determine exactly what imagery is needed.
2. **Fit Score:** Evaluates candidates deterministically against contextual, technical, and licensing criteria.
3. **Provenance Pack:** Maintains an audit trail tracking image origin, license, and processing actions.
4. **CMS Placement:** Produces a CMS-agnostic plan for where images should be injected.

## Extensibility (Adapters)

Pictovap uses an adapter-based architecture:
- **Image Sources:** Local folder, Unsplash, DepositPhotos, etc.
- **CMS Placement:** WordPress (working), Ghost (stub), Strapi (stub).
- **Metadata:** Gemini, Claude, LM Studio, or template fallbacks.

Read the [Adapter Architecture Overview](docs/adapters/overview.md) to learn how to extend the engine.

## Current Limitations

- Core logic was recently extracted from production; some internal dicts are still being typed.
- Demo uses mock assets rather than live API calls.
- Only WordPress adapter is production-hardened; others are reference implementations.

## Documentation

See the [Documentation Portal](docs/README.md) for full guides on architecture, concepts, and contribution.
