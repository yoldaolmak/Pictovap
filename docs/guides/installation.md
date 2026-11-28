# Installation

Full setup guide covering all Pictovap components.

## System Requirements

- macOS or Linux
- Python 3.10 or higher
- A CMS with an available adapter (WordPress, Ghost, or Strapi) — only if you intend
  to publish for real. None of this is required to run the demo.

## Install the published canonical release

For most users, one command installs the package and registers the
`actovisio-framework` CLI:

```bash
pip install actovisio-framework
actovisio-framework demo
```

That's it — the demo needs no credentials, no `.env`, and no network access.
The legacy `pictovap==0.13.0` release remains available on PyPI; the separate
`pictovap` 0.14.0 compatibility wheel is not published by the canonical release.

## Install from source (editable)

If you plan to modify ActoVisio Framework, install from a checkout in editable mode:

```bash
git clone https://github.com/yoldaolmak/ActoVisio-Framework.git
cd ActoVisio-Framework
python3 --version  # must be 3.10 or newer
python3 -m venv .venv
source .venv/bin/activate
make install
make contributor-smoke
```

The `make install` target installs Pictovap in editable mode with the test,
lint, and type-check dependencies, then `make contributor-smoke` verifies the
installed CLI, credential-free demo, and anonymous feedback flow. Before
opening a pull request, run the full contributor gate:

```bash
make contribution-check
```

This fast gate runs tests, Python lint/type checks, documentation link checks,
and security hygiene checks. `make quality` additionally runs Markdown linting
through `npx`.

## Verify Installation

```bash
actovisio-framework demo
```

This runs the full pipeline against a built-in sample article and deterministic
mock candidates. No `.env` file, no credentials, no network calls.

If you installed from source, you can also run the test suite:

```bash
make contribution-check
```

Expected: all checks passed.

## Optional: Configure Real Sources and Adapters

```bash
cp .env.example .env
```

Fill in only the sections you need — image source adapters (Unsplash,
DepositPhotos, a local folder) and/or a CMS adapter (WordPress, Ghost, Strapi).
See the [Configuration Reference](../reference/configuration.md) for every
available variable.

Once configured, run the pipeline against a real article:

```bash
actovisio-framework plan --article path/to/article.md --profile examples/profiles/sample-publisher.yaml --output plan.json --report report.md
```

## Troubleshooting

**`actovisio-framework: command not found`**
Make sure your virtualenv is active and the install completed
(`pip install -e .` from a source checkout; use `pictovap` only for the legacy 0.13.0 release).

**`plan` returns empty candidates**
Check that at least one entry in the profile's `image_sources` is actually configured
(e.g. `UNSPLASH_ACCESS_KEY` set, or `PICTOVAP_LOCAL_IMAGE_DIR` pointing at a real directory).
