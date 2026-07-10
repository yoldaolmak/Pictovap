# Installation

Full setup guide covering all Pictovap components.

## System Requirements

- macOS or Linux
- Python 3.9 or higher
- A CMS with an available adapter (WordPress, Ghost, or Strapi) — only if you intend
  to publish for real. None of this is required to run the demo.

## Step 1: Clone the Repository

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap
```

## Step 2: Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

The `-e` flag installs Pictovap in editable mode and registers the `pictovap` CLI command.

## Step 4: Verify Installation

```bash
pictovap demo
```

This runs the full pipeline against a built-in sample article and deterministic
mock candidates. No `.env` file, no credentials, no network calls.

```bash
python3 -m pytest tests/unit -v
```

Expected: all tests passed.

## Step 5 (Optional): Configure Real Sources and Adapters

```bash
cp .env.example .env
```

Fill in only the sections you need — image source adapters (Unsplash,
DepositPhotos, a local folder) and/or a CMS adapter (WordPress, Ghost, Strapi).
See the [Configuration Reference](../reference/configuration.md) for every
available variable.

Once configured, run the pipeline against a real article:

```bash
pictovap plan --article path/to/article.md --profile examples/profiles/sample-publisher.yaml --output plan.json --report report.md
```

## Troubleshooting

**`pictovap: command not found`**
Make sure your virtualenv is active and you ran `pip install -e .`.

**`plan` returns empty candidates**
Check that at least one entry in the profile's `image_sources` is actually configured
(e.g. `UNSPLASH_ACCESS_KEY` set, or `PICTOVAP_LOCAL_IMAGE_DIR` pointing at a real directory).
