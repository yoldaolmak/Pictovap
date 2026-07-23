# CLI Reference

Pictovap is a CLI-first tool. Commands emit JSON artifacts or diagnostics so
the same workflow can be reviewed by a person and composed in automation.

## Current Commands

### Identify the Installed Version

Print the exact package version when filing an issue, reproducing a plugin
problem, or recording a release check:

```bash
pictovap --version
```

### Run the Default Demo
Runs the local credential-free demo using the sample article and mock candidates.
```bash
pictovap demo
```
*(Also available via `python -m pictovap.demo` for backward compatibility).*

### Run with a File-Based Article
Executes the visual finishing pipeline on a specific Markdown article and outputs the canonical JSON plan. Markdown is the portable developer and static-site input; it is not required for WordPress editors.
```bash
pictovap plan \
  --article path/to/article.md \
  --profile examples/profiles/sample-publisher.yaml \
  --output output/plan.json
```

### Run with a WordPress Gutenberg Post

Reads one post through the WordPress REST API edit context, extracts Gutenberg
headings and surrounding text, and writes a visual plan. This command does not
modify the post, upload media, or publish anything.

```bash
pictovap plan \
  --wordpress-post 42 \
  --wordpress-site publisher \
  --output output/plan.json \
  --report output/report.md
```

`--wordpress-site publisher` reads `PUBLISHER_URL`, `PUBLISHER_USER`, and
`PUBLISHER_APP_PASSWORD`. Omit it to use the default `WP_` variables.

### Generate a Human-Readable Report
Generates an editor-readable Markdown report from an existing JSON plan.
An installed `pictovap.report_renderers` plugin can produce HTML or another
review format:
```bash
pictovap report \
  --plan output/plan.json \
  --output output/report.md

# Example third-party renderer
pictovap report --plan output/plan.json --output output/report.html --renderer html-review
```

### Create an Anonymous Validation Summary

When asking for help or reporting a result, create a small artifact that
contains only counts and runtime versions. It excludes article text, titles,
paths, URLs, profile names, and credentials:

```bash
pictovap feedback \
  --plan output/plan.json \
  --output output/feedback.json
```

The summary is also printed to stdout so it can be pasted directly into an
issue. Use it when you want to share diagnostics without sharing your article.

For GitHub issue comments, render the same anonymous summary as Markdown:

```bash
pictovap feedback \
  --plan output/plan.json \
  --format markdown \
  --output output/feedback.md
```

### Check an Installed Adapter

`pictovap adapter check` produces a machine-readable conformance report. The
default check constructs the adapter without calling a provider search or CMS
write, captures constructor diagnostics, and verifies that credential option
values were not emitted.

```bash
pictovap adapter check --kind renderer --name external-html-review
```

For a provider with a safe, bounded query, opt into candidate and provenance
field validation explicitly:

```bash
pictovap adapter check --kind provider --name local --exercise --count 3
```

The JSON report names each check and distinguishes `passed`, `not_run`, and
`not_applicable`; it never prints option values.

You can also generate it inline while planning:
```bash
pictovap plan \
  --article path/to/article.md \
  --profile examples/profiles/sample-publisher.yaml \
  --output output/plan.json \
  --report output/report.md
```

### Inspect Installed Adapter Plugins

Returns JSON metadata for independently installed adapter packages:

```bash
pictovap plugins
pictovap plugins --kind provider
pictovap plugins --kind cms
```

### Check Adapter Readiness

Loads every installed entry point and constructs adapters named explicitly.
It never calls `CMSAdapter.place`, so the command has no publishing effects:

```bash
pictovap doctor
pictovap doctor \
  --provider acme-images \
  --provider-option api_key=@ACME_IMAGES_API_KEY \
  --cms acme-cms \
  --cms-option base_url=https://cms.example.com \
  --cms-option token=@ACME_CMS_TOKEN
```

Only option names are included in JSON diagnostics. Values resolved from the
environment are not printed. The result also includes the Pictovap and Python
versions so a contributor can attach one safe diagnostic artifact to an issue.

### Plan with an Installed Provider

```bash
pictovap plan \
  --article path/to/article.md \
  --provider acme-images \
  --provider-option api_key=@ACME_IMAGES_API_KEY \
  --output output/plan.json
```

Candidates returned by the plugin are contract-validated before Fit Score.
An explicitly selected provider that returns no candidates produces an empty
candidate set; Pictovap does not hide the result by falling back to demo data.

### Preview or Execute CMS Placement

Start with a side-effect-free preview:

```bash
pictovap publish \
  --plan output/plan.json \
  --cms acme-cms \
  --cms-option base_url=https://cms.example.com \
  --cms-option token=@ACME_CMS_TOKEN \
  --dry-run
```

The dry run loads and constructs the adapter, rebuilds the typed
`CMSPlacement`, and prints the exact operations without calling `place`.
Remove `--dry-run` to execute the adapter. The returned `placed`, `failed`,
and `warnings` fields are validated before Pictovap reports completion.

### Generate an Adapter Plugin Package

Creates a standalone `src/`-layout Python project with entry-point metadata
and a passing contract test:

```bash
pictovap scaffold provider wikimedia
pictovap scaffold cms hugo --output path/to/projects
```

`--output` names the parent directory. The second command creates
`path/to/projects/pictovap-hugo`; change into that generated directory before
installing its dependencies.

The command refuses to overwrite existing scaffold files. Pass `--force` only
when intentionally refreshing files owned by the scaffold.
