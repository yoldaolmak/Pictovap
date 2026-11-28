# Decision Pack — editor review contract

An editor reviewing an article's images needs to see the proposed image for
each slot, its alternatives, why each candidate fits or fails, its provenance,
and where it might be placed. A Decision Pack groups this existing plan
evidence for review **without rerunning sources or modifying a CMS**.

```text
Validated Visual Plan → proposed Decision Pack
                      → editor accepts / replaces / rejects each slot
                      → reviewed Decision Pack → preview comparison
                      → separately authorized Product integration
```

## What the editor can decide

Each slot contains an editorial purpose, target heading, scored candidates,
intent evidence, and an optional proposal with candidate, provenance, and
placement bound together. Review decisions must identify the slot, action,
actor, and timestamp.

- **Accept:** retain the existing proposed asset and its evidence.
- **Replace:** choose a different scored candidate with complete provenance
  and placement bound to the same slot. New plans include eligible source-backed
  alternatives that the Gutenberg panel can select directly. The candidate's
  reported license remains evidence, not permission.
- **Reject:** leave the slot without an approved image.

A missing proposal cannot be accepted as valid evidence. Partially bound
assets, duplicate slot decisions, and mismatched filenames or candidate IDs
fail validation. License uncertainty remains visible for editor judgment;
a review decision does not grant image rights.

## What exists now

Schema 1 supports `pending` and `reviewed` states, validates completed
decisions and exposes a pure review transition helper in
`actovisio_framework.decision_pack`. It is experimental and side-effect-free.
New packs begin with:

```json
{
  "review": {"status": "pending", "decisions": []},
  "application": {"status": "not_applied", "receipts": []}
}
```

Application remains `not_applied` with no execution receipts even after a
review. The development CLI provides interactive
`actovisio-framework review --plan plan.json --actor editor --output reviewed.json`
and read-only `actovisio-framework review-preview` comparison. Editors can accept,
reject, or load an existing replacement evidence record; no CMS is contacted.
The [Gutenberg reference sidebar](../../examples/wordpress-review-sidebar/README.md)
offers an in-editor review draft without CMS writes. Use `review-pack` to
create its input and `review-import` to validate the downloaded draft's exact
source fingerprint and review evidence in Python Core. The sidebar alone
does not establish a valid reviewed pack or a licensed asset. See the
[CLI Reference](../reference/cli.md) and [Roadmap](../ROADMAP.md).

Build and validate a pack from an already validated Visual Plan:

```python
from actovisio_framework import build_decision_pack, validate_decision_pack

pack = build_decision_pack(plan)
result = validate_decision_pack(pack)
if result["status"] != "passed":
    raise ValueError(result["errors"])
```

A downstream publisher must independently authorize an actual CMS change,
record the action result, and verify the live outcome. See the
[Core/Product Contract](../architecture/core-product-boundary.md).
