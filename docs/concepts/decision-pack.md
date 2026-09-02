# Decision Pack

A Decision Pack is Pictovap's portable hand-off from planning to editorial
review. It is built from a validated visual plan, but it is not another
planning engine and does not rerun image sources, score candidates, or write to
a CMS.

```text
Visual plan evidence
  → Decision Pack (proposal by slot)
  → Editor review surface
  → Product integration boundary
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
or `reject` decision per slot, including an actor and timestamp. `accept`
retains the proposal's fully bound candidate, provenance, and placement.
`replace` must carry a different scored candidate with its own provenance and
placement, all bound to the same candidate and slot IDs. The placement output
filename must also match the filename recorded by provenance. It does not write
those decisions, apply a CMS change, create a rollback point, or claim that a
CMS action occurred.

An unfilled slot may keep all three proposal fields null while review is
pending. That slot can later be rejected or replaced, but it cannot be accepted
as if evidence existed. Partially populated proposal evidence is always invalid.

The `application` object is deliberately fixed to `not_applied` with an empty
receipt list. It prevents a Core review artifact from being mistaken for proof
of execution. Authorization, idempotency, rollback, execution receipts, and
live verification are owned by the separate Product lifecycle.

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
for the CMS-neutral core. The Core user flow ends at a reviewed preview:

```text
Plan → Review → Preview Diff → Product integration boundary
```

Schema 1 represents Plan and Review only. Product-owned execution must not be
implied by a pending or reviewed Decision Pack.
