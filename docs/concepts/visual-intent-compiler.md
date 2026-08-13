# Visual Intent Compiler

Pictovap's distinctive layer is not another image search endpoint. It is the
deterministic compiler between editorial intent and a CMS-ready visual plan.

```text
Article → Visual Intent Graph → Candidate Evidence → Constraints
        → Decision Ledger → Provenance Pack → CMS Placement
```

## Visual Intent Graph

The graph turns every image slot into an explicit editorial job. A slot carries
its role, target heading, query terms, and the constraints that a candidate
must satisfy. Hard constraints protect correctness: a usable license, a source
reference, and minimum dimensions. Soft constraints express quality: semantic
alignment, technical headroom, CMS suitability, and visual diversity.

The graph is deterministic and does not claim to infer a publisher's taste
from a hidden model. A publisher can inspect and version the resulting JSON.

## Decision Ledger

Every candidate-slot evaluation receives a ledger entry. It records:

- the final decision and human-readable reason
- hard and soft constraint status
- license, dimensions, provider, and source-reference evidence
- whether global selection assigned the candidate

This is a proof-carrying plan: an editor or adapter author can inspect why an
image was selected, rejected, or left for review without rerunning a provider.

Generate the explanation from an existing plan:

```bash
pictovap explain --plan output/plan.json --format markdown
pictovap explain --plan output/plan.json --format json --output output/intent-proof.json
```

The command is read-only. It never calls a provider, reads credentials, or
publishes to a CMS.

Validate the proof independently when an external tool stores or transports
the block:

```python
from pictovap import validate_intent_proof

result = validate_intent_proof(proof, expected_slot_ids=["featured", "inline-1"])
if result["status"] != "passed":
    raise ValueError(result["errors"])
```

The validator is side-effect-free and reports `intent_*` error codes for
schema, graph, ledger, assignment, and summary inconsistencies.

## Compatibility boundary

The `intent_proof` block is additive to the visual-plan JSON and has schema
version `1`. The initial contract is experimental while the compiler evolves;
external integrations should continue to depend on `pictovap.api`, adapter
protocols, and `validate_visual_plan()` as the stable foundation.
