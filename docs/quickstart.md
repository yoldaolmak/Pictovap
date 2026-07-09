# Quickstart

Get Pictovap running locally in under five minutes.

## Prerequisites

- Python 3.9+
- Git

## Installation

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Run the Local Demo

The demo requires no credentials, no external APIs, and no CMS connection.

```bash
make demo
```

Or directly:

```bash
python -m pictova.demo
```

This will:
1. Read `examples/sample-article.md`
2. Load a sample publisher profile
3. Load mock image candidates from `examples/assets/`
4. Create a Visual Brief
5. Evaluate candidates with Fit Scores
6. Create Provenance Packs for selected images
7. Create a CMS Placement plan
8. Write canonical JSON output to `examples/sample-output.json`
9. Print a terminal summary

To generate a human-readable visual plan report alongside the JSON, use the `--report` flag:

```bash
python -m pictova.demo --output examples/sample-output.json --report examples/sample-report.md
```

## Run Tests

```bash
source .venv/bin/activate
pytest
```

## Next Steps

- Read the Architecture Guide to understand the pipeline
- Explore the four primitives in docs/concepts/
- See Adapter Architecture to learn how to extend Pictovap
- Review Publisher Profiles to configure for your site
