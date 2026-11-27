# Working in Pictovap

This is the standing change contract, not a product roadmap or an operations
runbook. Product scope is defined in
[Core/Product Boundary](docs/architecture/core-product-boundary.md); current
priorities are in [Roadmap](docs/ROADMAP.md). Use live `main`, code, and CI
for implementation status, not hand-off notes or historical reports.

## Ownership and authority

- Confirm the current branch, open PRs, and affected files before editing.
  Work on a separate branch and avoid overriding another change owner.
- Change only authorized repository code and documentation. A visual plan or
  review is never permission to contact a provider, purchase an asset, change
  a CMS, or claim a published outcome.
- Framework is independently usable for one article and owns the shared
  visual decision implementation consumed by Product through stable released
  APIs. Enterprise inventory, lineage, permissions, execution and independent
  verification belong to Product; never import or disclose private Product IP.
- Version shared API/schema changes, test backward compatibility and release
  the Framework before Product adopts the new version.
- Keep documentation independent of any pilot publisher. Preserve source
  identities only in evidence, pilot records, and necessary technical links.

## Engineering invariants

- The planner returns data without printing or writing files. Render
  human-facing output from the same plan; `pictovap.api` is the public
  planning entry point.
- Provider failures and unavailable credentials are explicit source evidence,
  not successful observations. Preserve provenance, license uncertainty,
  source rights, and editor review requirements.
- Keep credential and data boundaries, path containment, URL validation, safe
  writes, and negative security tests intact. No CMS action or execution
  claim follows merely from validation, a dry run, or a review.
- Maintain public API/schema compatibility according to
  [API Stability](API_STABILITY.md). Code, docs, and commits are in English;
  article metadata may use supported content languages.
- Do not invent adoption, test, license, authorization, or customer evidence.

## Delivery

- Inspect a delegated diff yourself; verify its behavior independently.
- Run focused tests for changed behavior and `make contribution-check`;
  also run `make markdownlint` for Markdown changes and the
  [corpus benchmark](docs/concepts/golden-corpus.md) for planning changes.
- For packaging or release claims, build a wheel, install it in a clean
  environment, and test outside the source checkout. Editable installs alone
  do not prove distribution correctness.
- Never exercise credentials using an ad-hoc script that loads a real
  `.env`; isolate test values using pytest monkeypatch.
- Open a PR, review exact-head CI, and distinguish merge verification from
  test success. Do not claim live customer acceptance without independent
  live evidence.

Commands and environment setup belong in the
[Developer Guide](docs/DEVELOPER.md); user workflows belong in the
[Documentation Portal](docs/README.md).

## Interactive Continuation — Mandatory

Every user-facing final response in an ongoing GOAL-oriented session must end with one native, clickable **Devam et** button where supported. Its prompt must be dynamically determined through independent reasoning, never a fixed generic continuation loop.

- Evaluate the current GOAL, verified progress, unresolved problems, ownership and available evidence. Refresh relevant current sources only as needed. Understand the real problem and its root cause before choosing a solution.
- Compare viable alternatives (including reuse, deferral and no action) by goal impact, economic or user value, opportunity cost, feasibility, risk and authority. Select the highest-value authorized next whole outcome and complete it through meaningful verification.
- Preserve previous decisions, acceptance criteria and negative results. Challenge assumptions with counterevidence; distinguish evidence from hypotheses and proposals from verified outcomes.
- Never repeat completed work or mechanically retry blocked operations. Resolve root causes rather than introduce temporary workarounds. Prefer existing capabilities and the smallest durable solution.
- If blocked, investigate a genuinely different authorized path or advance another meaningful GOAL objective. Never create unnecessary tasks, infrastructure, experiments, status checks or reports merely to maintain activity.
- Replan when material evidence changes. Stop when the GOAL is complete, no worthwhile authorized work remains, or a genuine owner decision, grant or material risk is required. Report results, evidence, limitations and consequential decisions concisely.

The button must be last, after the result and limitations. Its submitted instruction must name the current GOAL or relevant unresolved problem, the next meaningful action and any material acceptance or authority constraints; use the actual evidence rather than a generic "continue" command. When no useful action remains, make continuation conditional on new decision-changing evidence or a new authorized GOAL; do not poll unchanged state. If native actions are unavailable, provide the same instruction in plain text and never fake a button. The action submits a new user turn; it does not itself execute work, run in the background, grant authority, authorize spending, disclosure or publication, or bypass existing security, scientific, legal, CI or human-acceptance gates. Scheduled reports need no button.

**Core continuation principle:** Continue toward the GOAL through independent judgment, not mechanical task execution.
