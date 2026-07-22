# API Stability Policy

Pictovap is beta software, but adapter authors need a dependable boundary.
This policy distinguishes the contracts that integrations may rely on from the
implementation modules that may change as the framework evolves.

The policy takes effect with the first published release that contains this
file. A security correction may override a compatibility promise when leaving
the old behavior in place would be unsafe.

## Stable Contracts

The following are stable public contracts. New optional fields may be added,
but required arguments, documented return fields, and contract meanings will
not change without a deprecation notice and migration guidance.

| Surface | What is stable |
|---|---|
| `pictovap.api` | `create_visual_plan()` and `create_wordpress_visual_plan()` keyword arguments and their JSON-shaped visual-plan output. |
| `pictovap` | The same two planning functions and the adapter protocols re-exported from the package root. |
| `pictovap.core.adapters` | `ImageSourceAdapter`, `CMSAdapter`, and `ReportRenderer`, including their documented method signatures. |
| Adapter data | The required candidate fields, CMS placement-result fields, and validation helpers published by `pictovap.testing`. |
| CMS plan types | `CMSPlacement` and `PlacementInstruction` serialization used by `CMSAdapter.place()`. |
| Publisher Profile v1 | `PublisherProfile`, `from_mapping()`, `from_yaml()`, and `publisher-profile-v1.schema.json`. |
| Plugin entry points | `pictovap.image_sources`, `pictovap.cms`, and `pictovap.report_renderers`. |

An adapter should depend only on these surfaces and use the contract assertions
in `pictovap.testing` in its own test suite.

## Experimental Surfaces

These are public and usable, but their behavior or shape may change in a
minor release while the framework is still pre-1.0:

- `pictovap.plugins` discovery helpers and plugin diagnostics
- `pictovap.scaffold` and generated-package templates
- built-in renderer presentation details in `pictovap.renderers`
- `pictovap.vision_templates`, including prompt wording and the optional
  `VisionTemplate.max_output_tokens` tuning field
- CLI convenience commands and their human-readable output
- built-in provider and CMS adapter implementation details

Experimental surfaces are appropriate for trying an integration. For a
published adapter, keep the integration boundary at the stable protocols and
entry points above.

## Internal Modules

Everything else under `pictovap.demo`, `pictovap.app`, `pictovap.engine`,
`pictovap.services`, `pictovap.providers`, `pictovap.publishers`, and
`pictovap.core` is internal unless named in the stable-contract table.
Do not import internal helpers from an external adapter.

## Compatibility Rules

- Patch releases do not intentionally break stable contracts.
- A stable-contract change requires a `Deprecated` entry in `CHANGELOG.md`,
  an actionable migration path, and at least one subsequent minor release in
  which the old path continues to work.
- New optional JSON fields and YAML fields are additive. Consumers must ignore
  fields they do not recognize.
- A new Publisher Profile schema version is a new contract. Pictovap will not
  reinterpret an existing schema version silently.
- Before a release, the project runs its public contract tests and a clean
  wheel-install smoke test. Third-party packages should pin a compatible
  Pictovap range and run their own contract tests in CI.

## Support Signals

If a stable contract needs clarification or appears to break, open an issue
with the Pictovap version, a minimal adapter or plan, and the expected versus
actual behavior. Maintainers will classify the report as a bug, documentation
gap, or proposal before changing the contract.
