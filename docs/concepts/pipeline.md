# The Pipeline

Pictovap's visual finishing pipeline moves an article through four stages.
Each stage produces a structured data object that feeds the next.

```
Visual Brief → Fit Score → Provenance Pack → CMS Placement
```

## Stages

### 1. Visual Brief

The pipeline starts by analyzing the article — its title, section headings,
and editorial context. The output is a `VisualBrief`: a structured description
of what imagery the article needs and where.

The parser is deterministic and rule-based. It does not call any AI API.

See: [Visual Brief](visual-brief.md)

### 2. Fit Score

For each image slot in the Visual Brief, the engine evaluates candidate images
across seven scoring dimensions: contextual relevance, section relevance, technical
quality, duplication risk, source trust, license confidence, and CMS suitability.

Each candidate receives a `FitScore` with a decision: `selected`, `rejected`,
or `needs_review`. The scoring is deterministic — no ML, no randomness.

See: [Fit Score](fit-score.md)

### 3. Provenance Pack

For every candidate that passes the Fit Score gate, a `ProvenancePack` is created.
This records the image's origin, license, processing actions, and generated metadata
(alt text, caption).

The Provenance Pack travels with the image through the rest of the pipeline.

See: [Provenance Pack](provenance-pack.md)

### 4. CMS Placement

The final stage produces a `CMSPlacement` plan: a CMS-agnostic description of
where each selected image should be injected into the article. A CMS-specific
adapter (WordPress, Ghost, Strapi, or others) reads this plan and executes the
native API calls.

WordPress is one CMS adapter among many. Nothing in the core pipeline is
WordPress-specific.

See: [CMS Placement](cms-placement.md)

## Running the Pipeline

Run the full pipeline with no credentials:

```bash
make demo
# or
python -m pictovap.demo
```

This runs all four stages against `examples/sample-article.md`, using mock candidate
images, and writes the output to `examples/sample-output.json`.

## Inspecting Intermediate State

Because each stage produces a serializable object, you can inspect the output at
any point:

```python
from pictovap.core.primitives import VisualBrief

brief = VisualBrief.from_markdown("examples/sample-article.md")
print(brief.to_dict())
```

## Engine Layout

```
src/
└── pictovap/
    ├── core/         # Primitives and shared data structures
    ├── engine/       # Pipeline orchestration
    ├── providers/    # Image source adapters
    ├── publishers/   # CMS placement adapters
    ├── profiles/     # Publisher configurations
    └── demo.py       # Local credential-free demo
```

## Compatibility Note

Product name: Pictovap.
The Python package is `pictovap` (since 0.3.0); `pictova` remains a deprecated alias.
