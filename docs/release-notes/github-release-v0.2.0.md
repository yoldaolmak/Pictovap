# Pictovap v0.2.0

Open-source visual finishing for content publishers.

## What this release includes

This is the first public baseline release. It makes the core pipeline runnable locally without any credentials or external APIs and provides the documentation, test suite, and contribution paths needed for external evaluation.

## Try it locally

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
make demo
```

## Core primitives

* Visual Brief
* Fit Score
* Provenance Pack
* CMS Placement

## Current limitations

* There is no external adoption yet. The system was extracted from dogfooding at a single publisher.
* The local demo uses deterministic mock/local candidates, not live sources.
* Only the WordPress CMS adapter is production-hardened; others are reference implementations.

## Good first contribution areas

* Add an Openverse image source adapter
* Add a Ghost or Strapi CMS placement adapter
* Add license confidence mapping to Provenance Pack

## Compatibility note

* The internal Python package namespace remains `pictova` for backward compatibility, while the product name is `Pictovap`.
