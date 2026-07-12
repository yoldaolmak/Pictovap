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

## Planned Commands

*Note: The following commands represent the planned CLI direction and are not currently implemented.*

- `pictovap plan <article.md>` — Generate a visual plan only.
- `pictovap publish <plan.json>` — Push a confirmed plan to a CMS via the configured adapter. Live publishing is adapter-dependent and not part of the credential-free demo.
