# Editor Report

Pictovap currently has no graphical user interface. It is a CLI-first open-source core. The intended review surface is an editor-readable report, while CMS adapters consume the JSON plan.

## JSON Output vs. Markdown Report

- **JSON Output**: The canonical machine-readable artifact containing the Visual Brief, Fit Scores, Provenance Packs, and CMS Placement instructions. This is for adapters and automation.
- **Markdown Report**: The editor-readable preview for humans.

Editors review the visual plan through a Markdown report, not raw JSON.

## Generating the Report

The report can be generated optionally using the `--report` flag during the demo execution:

```bash
python -m pictova.demo --article path/to/article.md --output my-plan.json --report my-report.md
```

## What the Report Contains

A premium editor report contains:
- Article Title, Language, and Publisher Profile summary
- Visual Brief structure (sections and required image slots)
- Selected image for each slot with generated alt text and captions
- Candidates Requiring Review (images that were rejected or flagged by the Fit Score rules)
- Provenance summary (license and source audit)
- CMS Placement Plan
- An Editorial Review Checklist for human sign-off
