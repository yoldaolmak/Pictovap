# Open-Source Readiness

This document tracks Pictovap's progress toward achieving open-source maturity and public infrastructure readiness.

## Current Status

Pictovap is a published early-stage open-source package. The public core and release path are working; adoption and independently validated usage remain the missing evidence.

## Current Evidence

- Public MIT-licensed repository
- Credential-free local demo
- Well-documented architecture and primitives
- Automated CI smoke tests and unit tests
- Clear release notes and changelog
- Contribution templates and starter issues
- Adoption playbook for early users
- Single-publisher dogfooding case study (Yoldaolmak)
- Tagged releases through v0.6.0
- Published `pictovap` package on PyPI
- Green main-branch CI and release workflows for v0.6.0
- CodeQL, dependency review, and OpenSSF Scorecard workflows
- Six external pull requests merged from five unique community contributors
- Third-party adapter discovery through standard Python entry points
- Public adapter contract tests and standalone plugin scaffolding
- Reproducible OpenSSF Criticality Score workflow with a pinned tool checksum

## Missing Ecosystem Signals

- Additional external contributors and sustained review activity
- External publisher case studies
- Meaningful package downloads/usage
- Dependent projects or integrations
- External issues reported by real users
- Third-party validation or mentions
- OpenSSF Scorecard improvements
- A Criticality Score of at least 0.4 (latest measured snapshot: 0.21280 on 2026-07-22)

## Public Maturity Milestones

The release infrastructure is live. The goals for the next maturity milestone are:

- Continue merging external contributions only after their acceptance criteria pass.
- Keep the main-branch and release workflows green.
- Receive a reproducible field report from an external publisher.
- Add a second publisher profile that demonstrates a distinct use case.
- Receive and merge independently implemented adapter plugins or in-tree adapters.
- Establish sustained release and maintenance cadence beyond the initial launch.

## Risks

- External contribution is still early and concentrated in five contributors.
- Package usage and downstream dependents are not yet established.
- Single-publisher dogfooding only; no independent validation.
- Limited CI coverage for integration paths.

## Next Steps

1. Publish the prepared launch announcements and invite reproducible demo feedback.
2. Direct provider and CMS contributors to the v0.6.0 scaffold, runtime, and contract test kit.
3. Document a second publisher profile to demonstrate generality.
4. Monitor branch protection, CodeQL, dependency review, OpenSSF Scorecard, and the
   [Criticality Score workflow](https://github.com/yoldaolmak/Pictovap/actions/workflows/criticality.yml).
5. Track real package usage, external reports, and downstream integrations without proxy claims.

*Note: Pictovap is still early and does not yet claim broad ecosystem adoption or third-party validation.*
