# CLI Reference

Pictovap is a CLI-first tool. The primary execution surface currently is the demo module, which runs the pipeline locally without requiring API credentials or external dependencies.

## Current Commands

### Run the Default Demo
Runs the local credential-free demo using the sample article and mock candidates.
```bash
pictovap demo
```
*(Also available via `python -m pictovap.demo` for backward compatibility).*

### Run with a Custom Article
Executes the visual finishing pipeline on a specific Markdown article and outputs the canonical JSON plan.
```bash
pictovap plan \
  --article path/to/article.md \
  --profile examples/profiles/sample-publisher.yaml \
  --output output/plan.json
```

### Generate a Human-Readable Report
Generates an editor-readable Markdown report from an existing JSON plan.
```bash
pictovap report \
  --plan output/plan.json \
  --output output/report.md
```

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

### Generate an Adapter Plugin Package

Creates a standalone `src/`-layout Python project with entry-point metadata
and a passing contract test:

```bash
pictovap scaffold provider wikimedia
pictovap scaffold cms hugo --output path/to/projects
```

The command refuses to overwrite existing scaffold files. Pass `--force` only
when intentionally refreshing files owned by the scaffold.

## Planned Commands

*Note: The following commands represent the planned CLI direction and are not currently implemented.*

- `pictovap publish <plan.json>` — Push a confirmed plan to a CMS via the configured adapter. Live publishing is adapter-dependent and not part of the credential-free demo.
