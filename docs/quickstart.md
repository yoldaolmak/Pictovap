# Quickstart

Get Pictovap running locally in under five minutes.

## 1. What is Pictovap?

Pictovap is an open-source visual finishing engine for content publishers.

It turns unfinished articles into visually complete, rights-aware, publish-ready CMS pages.

It reads article structure, creates a Visual Brief, evaluates candidate images with Fit Scores, records Provenance Packs, generates metadata, and prepares CMS Placement instructions.

## 2. Installation

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## 3. Run the Local Demo

You do not need WordPress credentials to run the local demo.
You do not need image provider credentials to run the local demo.

The demo requires no credentials, no external APIs, and no CMS connection. The demo uses deterministic local/mock candidates.

```bash
pictovap demo
```

Or using the legacy module syntax:

```bash
python -m pictovap.demo
```

This will:
1. Read an example article
2. Load a sample publisher profile
3. Evaluate mock images
4. Create a JSON output (canonical machine-readable artifact for adapters and automation)
5. Create a Markdown report (editor-readable preview for humans)

## 4. Next Steps

- Read [Using Pictovap](guides/using-pictovap.md) for the full user journey
- See [CLI Reference](reference/cli.md) to run it against your own files
