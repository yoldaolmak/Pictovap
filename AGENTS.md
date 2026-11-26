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

## Interactive GPT continuation
In interactive ChatGPT web/app sessions, finish the next consequential authorized task or coherent milestone, then end the response with one native **Devam et** action button submitting `Devam. Sıradaki yetkili görevi yürüt; tamamlanmış işleri tekrarlama.` If native actions are unavailable, offer that exact text plainly; never fake a button. On continuation re-read current main, active goal, owners and evidence; preserve completed work. This is convenience only, not additional authority, mandatory approval, background execution, or permission to bypass existing gates. Stop at genuine blockers with no safe next task; scheduled reports need no button.
