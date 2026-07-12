# Fit Score

The **Fit Score** is the second core primitive in the Pictovap pipeline.
It provides a transparent, auditable mechanism for evaluating candidate images
against a `VisualBrief`.

Instead of opaque "magic" matching, every candidate image receives a broken-down
score across seven independent dimensions. This allows publishers to understand,
audit, and tune why a specific image was selected or rejected.

## Dimensions

A `FitScore` evaluates:

| Dimension | What It Measures |
|---|---|
| `contextual_relevance` | Keyword overlap with article topic and title |
| `section_relevance` | Keyword overlap with the target section heading |
| `technical_quality` | Resolution and aspect ratio suitability |
| `duplication_risk` | Whether the image has been used recently in other articles |
| `source_trust` | Preference for owned photography over stock |
| `license_confidence` | Whether the image is confirmed safe to use commercially |
| `cms_suitability` | Whether it fits required dimensions for the CMS theme |

## Decisions

After scoring, each candidate receives one of three decisions:

- **`selected`** — strong fit; proceed to Provenance Pack
- **`rejected`** — fails a hard criterion (e.g., resolution too low, license unclear)
- **`needs_review`** — moderate fit; flagged for human review

Hard failures (low resolution, unknown license) short-circuit scoring and produce an
immediate `rejected` decision with an explanatory reason.

## Scoring Is Deterministic

The scoring algorithm is rule-based and deterministic. It is not ML. Given the same
inputs, it produces the same output. This makes it:

- **Auditable** — you can trace every decision
- **Testable** — unit tests cover the full decision tree
- **Tunable** — weights can be adjusted per publisher profile

## Extending Scoring

While the current engine uses rule-based heuristics, the `FitScore` primitive is designed so that future adapters can extend or replace scoring logic (e.g., using a local lightweight ML model for aesthetic grading) as long as they return the deterministic `FitScore` object.

## Example

```python
from pictovap.core.primitives import FitScore

score = FitScore(
    candidate_id="img-001",
    contextual_relevance=2.0,
    technical_quality=3.0,
    license_confidence=2.0,
    final_score=12.5,
    decision="selected",
    human_reason="Strong fit: contextual=2.0, quality=3.0, license=2.0"
)

print(score.to_dict())
```

## Where It Feeds

Selected candidates from FitScore pass into the `ProvenancePack` stage.
Rejected candidates are logged with their reason.

**Source:** `src/pictovap/core/primitives.py` — `FitScore` class.
