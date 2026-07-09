# CLI Reference

Pictovap is a CLI-first tool. The primary execution surface currently is the demo module, which runs the pipeline locally without requiring API credentials or external dependencies.

## Current Commands

### Run the Default Demo
Runs the local credential-free demo using the sample article and mock candidates.
```bash
python -m pictova.demo
```

### Run with a Custom Article
Executes the visual finishing pipeline on a specific Markdown article and outputs the canonical JSON plan.
```bash
python -m pictova.demo --article path/to/article.md --output output/plan.json
```

### Generate a Human-Readable Report
Executes the pipeline and simultaneously generates an editor-readable Markdown report alongside the JSON plan.
```bash
python -m pictova.demo --article path/to/article.md --output output/plan.json --report output/report.md
```

## Planned Commands

*Note: The following commands represent the planned CLI direction and are not currently implemented.*

- `pictovap plan <article.md>` — Generate a visual plan only.
- `pictovap publish <plan.json>` — Push a confirmed plan to a CMS via the configured adapter.
