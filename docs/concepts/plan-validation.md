# Visual plan validation

Pictovap plans are designed to be passed between independent tools. The
`validate_visual_plan()` API and `pictovap validate` command provide a
side-effect-free boundary for checking those hand-offs before a report or CMS
adapter consumes them.

## Python API

```python
from pictovap import validate_visual_plan

result = validate_visual_plan(plan)
if result["status"] != "passed":
    raise ValueError(result["errors"])
```

The result is JSON-serializable and contains `checks`, structured `errors`,
recommended `warnings`, and a compact `summary`. Validation never contacts a
provider, reads credentials, writes files, or calls a CMS.

## CI and CLI

```console
pictovap validate --plan output/visual-plan.json
pictovap validate --plan output/visual-plan.json --strict
```

The command exits zero when the plan passes. Strict mode also fails when
recommended audit information is incomplete, such as missing planning
diagnostics or a provenance record without a CMS placement.

The stable core checks cover the visual brief, fit-score records, provenance
packs, and CMS placement instructions. New additive fields are ignored so an
adapter can remain compatible across minor releases.

For a human-readable readiness review that also checks coverage,
accessibility, license status, and duplicate selections, use the
[plan audit](plan-audit.md) boundary.
