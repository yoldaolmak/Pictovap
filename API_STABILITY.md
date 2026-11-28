# API Stability Policy

The concise external-facing ABI summary is maintained in
[FRAMEWORK_COMPATIBILITY.md](FRAMEWORK_COMPATIBILITY.md). This document keeps
the detailed surface-by-surface policy and migration rules.

ActoVisio Framework is beta software, but adapter authors need a dependable boundary.
This policy distinguishes the contracts that integrations may rely on from the
implementation modules that may change as the framework evolves.

The policy takes effect with the first published release that contains this
file. A security correction may override a compatibility promise when leaving
the old behavior in place would be unsafe.

The 0.14.0 candidate adds the canonical namespace. The legacy compatibility
wheel retains the old public imports and command with one implementation;
0.13.0 remains available. Serialized kind names and plugin groups are unchanged.

## Stable Contracts

The following are stable public contracts. New optional fields may be added,
but required arguments, documented return fields, and contract meanings will
not change without a deprecation notice and migration guidance.

| Surface | What is stable |
|---|---|
| `actovisio_framework.api` | `create_visual_plan()` and `create_wordpress_visual_plan()` keyword arguments and their JSON-shaped visual-plan output. |
| `actovisio_framework` | The same two planning functions and the adapter protocols re-exported from the package root. |
| `actovisio_framework.core.adapters` | `ImageSourceAdapter`, `CMSAdapter`, and `ReportRenderer`, including their documented method signatures. |
| `actovisio_framework.core.selection` | `SelectionPolicy`, `SelectionResult`, and `select_assignments()`, including optional candidate fingerprints and additive diversity diagnostics. |
| `actovisio_framework.core.visual_similarity` | `compute_visual_fingerprint()` and `visual_similarity()` for deterministic, local-only editorial diversity signals. |
| `actovisio_framework.validation` | `validate_visual_plan()` for side-effect-free validation of serialized plans in CI and external integrations. |
| `actovisio_framework.decision_pack` | From 0.13.0: schema 1, `build_decision_pack()`, `validate_decision_pack()`, `transition_decision_pack_review()`; no input mutation or CMS authority. |
| `actovisio_framework.intent_validation` | From 0.13.0: `validate_intent_proof()` and schema 1 validation result. |
| Adapter data | The required candidate fields, CMS placement-result fields, and validation helpers published by `actovisio_framework.testing`. |
| `actovisio_framework.testing` fixtures | Deterministic, JSON-safe fixtures: `sample_candidate()`, `sample_placement()`, `sample_visual_plan()`, and `sample_decision_pack()`. |
| CMS plan types | `CMSPlacement` and `PlacementInstruction` serialization used by `CMSAdapter.place()`. |
| Publisher Profile v1 | `PublisherProfile`, `from_mapping()`, `from_yaml()`, and `publisher-profile-v1.schema.json`. |
| Plugin entry points | `pictovap.image_sources`, `pictovap.cms`, and `pictovap.report_renderers`. |

An adapter should depend only on these surfaces and use the contract assertions
in `actovisio_framework.testing` in its own test suite (`actovisio_framework.testing` provides
`sample_visual_plan()` and `sample_decision_pack()` alongside `sample_candidate()`
and `sample_placement()`).

## Experimental Surfaces

These are public and usable, but their behavior or shape may change in a
minor release while the framework is still pre-1.0:

- `actovisio_framework.plugins` discovery helpers and plugin diagnostics
- `actovisio_framework.scaffold` and generated-package templates
- built-in renderer presentation details in `pictovap.renderers`
- `actovisio_framework.vision_templates`, including prompt wording and the optional
  `VisionTemplate.max_output_tokens` tuning field
- `actovisio_framework.intent` compiler helpers beyond the stable schema-1 validation contract
- `actovisio_framework.registry` metadata and registry presentation details
- `actovisio_framework.plan_diff`, the plan-diff schema, and Markdown presentation details
- CLI convenience commands and their human-readable output
- built-in provider and CMS adapter implementation details

Experimental surfaces are appropriate for trying an integration. For a
published adapter, keep the integration boundary at the stable protocols and
entry points above.

## Internal Modules

Everything else under `actovisio_framework.demo`, `actovisio_framework.app`, `actovisio_framework.engine`,
`actovisio_framework.services`, `pictovap.providers`, `actovisio_framework.publishers`, and
`actovisio_framework.core` is internal unless named in the stable-contract table.
Do not import internal helpers from an external adapter.

`actovisio_framework.api` is the only supported way to create a visual plan from Python.
The planning engine behind it (`actovisio_framework.engine.planner`) is internal and may
move; `actovisio_framework.demo` is a runner for the credential-free example and exposes
no planning API of its own.

## Compatibility Rules

- Patch releases do not intentionally break stable contracts.
- A stable-contract change requires a `Deprecated` entry in `CHANGELOG.md`,
  an actionable migration path, and at least one subsequent minor release in
  which the old path continues to work.
- New optional JSON fields and YAML fields are additive. Consumers must ignore
  fields they do not recognize. Schema-1 decision and intent validation may
  reject unsafe or inconsistent evidence; a security correction is not a
  reason to silently reinterpret historical records.
- The Product integration pins a released Framework version and runs
  differential, retained-evidence and clean-wheel tests before upgrading.
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
