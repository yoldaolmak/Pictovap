# pictovap-hugo

Runnable Hugo CMS adapter example for Pictovap.

This package shows how a third-party CMS adapter can consume Pictovap's
`CMSPlacement` contract without modifying Pictovap core. It writes Hugo
`figure` shortcodes into Markdown files under a configured content directory.
The example is intentionally local-first: no credentials, network calls, or
Hugo binary are required.

## Install and Test

From this directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
pytest
pictovap plugins --kind cms
pictovap adapter check --kind cms --name hugo
```

## Preview a Pictovap Plan

`publish --dry-run` validates the installed adapter and shows the planned
operations without writing content:

```bash
pictovap publish --plan plan.json --cms hugo --dry-run \
  --cms-option content_dir=content
```

## Write to a Local Hugo Content Tree

The adapter maps `CMSPlacement.article_id` to a Markdown path inside
`content_dir`. For example, `article_id="posts/sample.md"` writes to
`content/posts/sample.md`. Paths that escape `content_dir` are rejected.

```bash
pictovap publish --plan plan.json --cms hugo \
  --cms-option content_dir=content \
  --cms-option assets_prefix=/images/pictovap
```

Each inserted block is wrapped in stable markers:

```markdown
<!-- pictovap:section_0:start -->
{{< figure src="/images/pictovap/market.webp" alt="Market stall" caption="Local market" >}}
<!-- pictovap:section_0:end -->
```

Running the same plan again replaces the marked block instead of inserting a
duplicate shortcode.

## What to Reuse in a Real Adapter

- Entry point: `[project.entry-points."pictovap.cms"]`
- Contract test: `assert_cms_adapter_contract`
- Path containment before file writes
- Idempotent markers around generated CMS output
- A dry-run workflow before any production write
