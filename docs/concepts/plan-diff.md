# Visual Plan Diff

Editorial plans change for different reasons: the article structure may have
changed, a publisher profile may apply different rules, the provider may have
returned a different candidate pool, or CMS placement metadata may have been
edited. A raw JSON diff mixes those causes together and makes review harder.

Pictovap's plan diff groups them into explicit, deterministic categories:

- article identity, fields, and image-slot topology;
- publisher-profile fields;
- candidate additions, removals, and per-slot evaluation changes;
- selected-image and provenance changes;
- CMS placement changes;
- compiled intent and planning-diagnostic changes.

## Compare Two Plans

```bash
pictovap diff \
  --before output/plan-before.json \
  --after output/plan-after.json \
  --format markdown \
  --output output/plan-diff.md
```

Use JSON when another tool needs the structured receipt:

```bash
pictovap diff \
  --before output/plan-before.json \
  --after output/plan-after.json \
  --format json \
  --output output/plan-diff.json
```

The command returns exit status `0` whether the plans are unchanged or changed.
That default makes an editorial difference reviewable rather than treating it
as an execution error. Add `--fail-on-change` for a CI drift gate; a detected
change then returns exit status `1` after the complete diff is written.

## Python API

```python
from pictovap import diff_visual_plans, render_plan_diff_markdown

result = diff_visual_plans(before_plan, after_plan)
if result["status"] == "changed":
    print(render_plan_diff_markdown(result))
```

The result uses plan-diff schema version `1`. Its `change_sources` field
attributes differences to `article`, `profile`, `candidates`, `policy`, or
`cms_placement`. `input_validation` also records whether each source plan
passes the existing visual-plan validator, so a reviewer can distinguish plan
drift from malformed input.

## Safety Boundary

Plan diff reads only the two supplied JSON documents. It does not rerun image
providers, load publisher credentials, inspect the original article, re-score
candidates, write to a CMS, or claim why an upstream input changed. It reports
the evidence present in the serialized plans.

Volatile runtime metadata and local source paths are intentionally excluded
from the comparison. Candidate score components, provenance, intent
constraints, decision-ledger evidence, alt text, captions, and placement
instructions are included because they can change an editorial decision or
downstream CMS behavior.

The schema is experimental before Pictovap 1.0. Consumers should check
`schema_version`, accept additive fields, and avoid parsing the Markdown
presentation as a machine contract.
