# Editor Report

Pictovap currently has no graphical user interface. It is a CLI-first open-source core. The intended review surface is an editor-readable report, while CMS adapters consume the JSON plan.

## JSON Output vs. Markdown Report

- **JSON Output**: The canonical machine-readable artifact containing the Visual Brief, Fit Scores, Provenance Packs, and CMS Placement instructions. This is for adapters and automation.
- **Markdown Report**: The editor-readable preview for humans.

Editors review the visual plan through a Markdown report, not raw JSON.

## Generating the Report

The report can be generated either from an existing JSON plan:

```bash
pictovap report --plan my-plan.json --output my-report.md
```

Or generated optionally using the `--report` flag during the planning phase:

```bash
pictovap plan \
  --article path/to/article.md \
  --profile examples/profiles/sample-publisher.yaml \
  --output my-plan.json \
  --report my-report.md
```

## What the Report Contains

A premium editor report contains:
- **Article Details** — Title, detected language, article source path, and Publisher Profile summary
- **Visual Brief structure** — Detected sections, required image slots, preferred image type per slot, and section excerpts/context if available
- **Selected image for each slot** — Selected candidates with localized, non-generic alt text and captions, along with their fitness scores and selection reasons
- **Candidates Requiring Review** — Images that were rejected or flagged by the Fit Score rules (with candidate ID, slot, reason, and score)
- **Provenance summary** — License status, provider, source URL/local path, attribution, and content hash audit
- **CMS Placement Plan** — Placement strategy, target section, image role, and output path
- **An Editorial Review Checklist** — Human sign-off steps to verify context, alt text, license, and placement before live publishing
