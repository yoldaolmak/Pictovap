# Selection Engine

Pictovap scores every image candidate against every editorial slot, then makes
one global assignment decision. This is deliberately separate from scoring:
the score explains *why* an image fits, while the selection engine decides
*where* it should be used.

## Why global selection matters

A greedy planner can assign the same strong candidate to the first two slots
and leave a later section empty. Pictovap's default policy prevents that. It
solves a deterministic maximum-weight assignment across eligible candidates,
so the total fit of the complete article is considered together.

The default policy:

- accepts only candidates with a selected Fit Score and a score of at least
  `8.0`;
- uses each candidate at most once;
- keeps unfilled slots visible instead of silently reusing an image;
- reports coverage and warnings in `planning_diagnostics`.
- applies an optional perceptual-similarity penalty when candidates provide a
  `visual_fingerprint`, so an article does not quietly receive several near-
  duplicate images.

## Diagnostics

Every generated plan contains a `planning_diagnostics` object:

```json
{
  "algorithm": "deterministic_maximum_weight_assignment",
  "slots_requested": 3,
  "slots_filled": 3,
  "coverage_ratio": 1.0,
  "total_score": 28.4,
  "adjusted_total_score": 27.1,
  "diversity_penalty": 1.3,
  "similarity_pairs": [
    {"left_candidate_id": "img-1", "right_candidate_id": "img-2", "similarity": 0.98, "penalty": 1.3}
  ],
  "unfilled_slots": [],
  "warnings": []
}
```

This gives a CMS adapter or editor UI a safe quality boundary. A plan with
`coverage_ratio < 1.0` is still valid JSON, but it is visibly incomplete and
can be held for review before publishing.

## Adapter usage

The engine is public for external providers that want the same decision policy:

```python
from pictovap import select_assignments

result = select_assignments(scores_by_slot)
if result.coverage_ratio < 1.0:
    raise RuntimeError("The article needs editorial image review")
```

Adapters that already have local image files can expose fingerprints and let
the engine account for visual variety:

```python
from pictovap import compute_visual_fingerprint, select_assignments

fingerprints = {
    candidate["id"]: compute_visual_fingerprint(candidate["local_path"])
    for candidate in candidates
    if candidate.get("local_path")
}
result = select_assignments(scores_by_slot, candidate_fingerprints=fingerprints)
```

Missing or invalid fingerprints are ignored. Pictovap never fetches a remote
image merely to calculate similarity.

For a deliberately small candidate pool, an integration can opt into reuse:

```python
from pictovap import SelectionPolicy, select_assignments

result = select_assignments(
    scores_by_slot,
    policy=SelectionPolicy(allow_candidate_reuse=True),
)
```

Reuse is explicit so a downstream publisher never inherits a hidden content
duplication policy.
