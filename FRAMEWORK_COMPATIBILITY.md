# Framework Compatibility

Pictovap publishes a small compatibility contract for people building image
sources, CMS integrations, renderers, and publisher profiles outside this
repository. The detailed policy lives in [API Stability](API_STABILITY.md).

## Framework ABI v1

The following surfaces are stable for the current pre-1.0 framework line:

- `pictovap.api.create_visual_plan()` and `create_wordpress_visual_plan()`
- `ImageSourceAdapter`, `CMSAdapter`, and `ReportRenderer` protocols
- `pictovap.testing.contracts` assertions and complete candidate fields
- visual-plan JSON sections required by `pictovap.validate_visual_plan()`
- Publisher Profile YAML schema version 1
- installed adapter entry-point groups (`pictovap.providers`,
  `pictovap.cms`, and `pictovap.renderers`)

The golden corpus benchmark and its CLI are integration tooling. They are
stable for this repository's contributor and CI workflow, but the benchmark
module is not yet a versioned third-party ABI.

The read-only `pictovap registry list` command is also discovery tooling. Its
JSON shape is versioned as schema 1 for this release line, but adapter authors
should continue to depend on the adapter protocols and entry-point groups,
not on registry presentation details.

The additive `intent_proof` plan block is experimental schema 1. It exposes the
Visual Intent Graph and Decision Ledger for review and tooling. Integrations
must tolerate its absence and must not treat the proof as a legal license
guarantee; it is a structured record of the evidence Pictovap observed.

## Compatibility rules

- Pictovap supports Python 3.10 and newer.
- Patch releases fix bugs and do not intentionally break the stable surfaces.
- Minor releases may add optional fields, methods, or adapter capabilities.
- Required-field or serialized-schema changes are preceded by a deprecation
  period and migration notes.
- A breaking change is reserved for a future major release and is documented
  in the changelog before release.
- Additive JSON and YAML fields must not invalidate an older consumer.
- A stable adapter should pin a compatible minor line, for example
  `pictovap>=0.13,<0.14`, and run the contract tests in its own CI.

## Adapter author checklist

Before publishing an adapter, run the following locally:

```bash
pip install pictovap
pictovap adapter check --kind provider --name your-provider --exercise
python -m pytest tests -q
```

For a CMS adapter, use `--kind cms`; for a report renderer, use
`--kind renderer`. Keep credentials out of fixtures and use dry-run paths for
integration tests. A third-party adapter should document the Pictovap minor
line it supports and the exact contract-test version used.

## What is not a compatibility promise

Implementation modules under `pictovap.demo`, `pictovap.services`,
`pictovap.providers`, and `pictovap.publishers` may evolve behind the stable
interfaces. Internal helper functions, CLI wording, and diagnostic detail are
not an ABI. Use the public API and adapter protocols rather than importing
pipeline internals.
