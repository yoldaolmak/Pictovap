# Decision Pack

A Decision Pack is Pictovap's portable hand-off from planning to editorial
review. It is built from a validated visual plan, but it is not another
planning engine and does not rerun image sources, score candidates, or write to
a CMS.

```text
Visual plan evidence
  → Decision Pack (proposal by slot)
  → Editor review surface
  → Future preview and CMS application receipt
```

## What it carries

For each image slot, schema 1 groups:

- the editorial purpose and target heading;
- every scored candidate already present in the plan;
- the proposed selected asset, provenance record, and placement instruction;
- any compiled intent-ledger evidence already present in the plan.

It also reserves distinct top-level state for review and application. This
separation prevents a user interface from presenting a proposed placement as if
it had been accepted or published.

## Current boundary

Decision Pack schema 1 is experimental and read-only. A newly built pack has:

```json
{
  "review": {"status": "pending", "decisions": []},
  "application": {"status": "not_applied", "receipts": []}
}
```

The validator recognizes a complete editor review with one `accept`, `replace`,
or `reject` decision per slot, including an actor and timestamp. It does not
yet write those decisions, apply a CMS change, create a rollback point, or
claim that a CMS action occurred. Those operations require later additive
contracts and explicit user authorization.

## Python API

```python
from pictovap import build_decision_pack, validate_decision_pack

pack = build_decision_pack(plan)
result = validate_decision_pack(pack)
if result["status"] != "passed":
    raise ValueError(result["errors"])
```

Both functions are side-effect-free. The source visual plan must already pass
`validate_visual_plan()` before a pack can be built.

## Product role

Pictovap Core is the planning and evidence layer. A WordPress Gutenberg
integration is the first intended reference review surface, not a replacement
for the CMS-neutral core. The intended user flow is:

```text
Plan → Review → Preview Diff → Apply → Receipt
```

Only the first two stages are represented by schema 1. The remaining stages
are roadmap work and must not be implied by a pending Decision Pack.
