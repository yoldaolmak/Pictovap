# Plan audit

`audit_visual_plan()` is the final local review boundary before a plan reaches
a CMS adapter. It does not contact providers, read credentials, write files,
or publish content.

```python
from pictovap import audit_visual_plan

audit = audit_visual_plan(plan)
if audit["status"] == "failed":
    raise ValueError(audit["checks"])
```

The report combines the public structural validator with practical editorial
signals:

- requested versus placed slots and coverage;
- selected, rejected, and still-unreviewed candidates;
- provenance records and known license status;
- non-empty alt text on CMS placement instructions;
- duplicate candidate selections across slots.

Draft plans return `warning` when a review decision is still needed. Use
`strict=True` in CI, or `pictovap audit --strict`, when those warnings must
block a hand-off.

The Markdown form is useful for a human editor:

```bash
pictovap audit \
  --plan output/visual-plan.json \
  --format markdown \
  --output output/plan-audit.md
```
