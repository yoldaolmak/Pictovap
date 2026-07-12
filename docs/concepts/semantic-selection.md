# Candidate Selection

Candidate selection is the process by which Pictovap determines which images fit a
given article slot. It operates within the Fit Score stage of the pipeline.

## The Core Problem

An article about minimalist travel should get photos of backpacks, trails, and
organized luggage — not tourist landmark panoramas or generic cityscapes. An article
about Istanbul should get photos with the right geographic context. This requires
understanding the article's content, not just matching a single keyword to a filename.

## How Fit Scoring Works

### Step 1: Context From the Visual Brief

The Visual Brief provides the selection context:

- **Article topic** — the thematic focus (e.g., "minimalist travel")
- **Section headings** — the specific section this image slot serves
- **Editorial preferences** — from the publisher profile

### Step 2: Keyword Scoring

The engine scores each candidate's keywords against the article context:

- **Contextual relevance** — overlap with the article topic and title
- **Section relevance** — overlap with the target section heading

### Step 3: Technical Gate

Technical quality is evaluated against minimum thresholds:

- Resolution (minimum width and height for the target slot)
- Aspect ratio suitability for the CMS layout
- Blur and exposure (when metadata is available)

Candidates below the technical minimum receive a `rejected` decision immediately,
regardless of contextual score.

### Step 4: License and Trust

- **License confidence** — whether the license is confirmed and commercially safe
- **Source trust** — preference for owned and locally indexed images over stock APIs

Candidates with unclear licenses receive a `rejected` decision regardless of other scores.

### Step 5: Decision

After all dimensions are scored, each candidate receives a decision:

| Decision | Criteria |
|---|---|
| `selected` | Final score above threshold; all hard gates passed |
| `rejected` | Failed a hard gate (resolution, license) |
| `needs_review` | Passed hard gates but score is moderate; flagged for human review |

## Inspecting Scores

Run `make demo` to see the full score breakdown for all candidates across all slots:

```
Slot 'featured':
  ✓ img-backpack-01: 12.5 (selected) — Strong fit: contextual=2.0, quality=3.0, license=2.0
  ✓ img-forest-02:   10.5 (selected) — Strong fit: contextual=0.0, quality=3.0, license=2.0
  ✗ img-lowres-04:   9.0  (rejected) — Resolution too low (320x240)
  ? img-generic-03:  7.0  (needs_review) — Moderate fit, manual review recommended
```

## Tuning Selection

Selection behavior is controlled by the publisher profile. Relevant fields:

| Field | Effect |
|---|---|
| `image_sources` | Which adapters supply candidates |
| `forbidden_patterns` | Keywords causing immediate rejection |
| `editorial_preferences` | Contextual weighting hints |

See [Publisher Profiles](../reference/publisher-profiles.md) for configuration details.

## Compatibility Note

Product name: Pictovap.
The Python package is `pictovap` (since 0.3.0); `pictova` remains a deprecated alias.
