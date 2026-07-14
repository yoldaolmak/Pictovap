# Pictovap Adapter Sprint — July 2026

Pictovap 0.5.0 introduced third-party plugin discovery, reusable adapter
contract tests, and a scaffold command. This sprint tests that contribution
path with real provider and CMS integrations.

The sprint starts on July 14, 2026. We will review the first checkpoint on
July 21 and the 30-day checkpoint on August 13. The issues remain valid after
those dates; the dates are measurement boundaries, not artificial deadlines.

## Available Tracks

| Track | Issue | Credentials | Best fit |
| --- | --- | --- | --- |
| Wikimedia Commons provider | [#2](https://github.com/yoldaolmak/Pictovap/issues/2) | None | Open-data and licensing contributors |
| Pixabay provider | [#1](https://github.com/yoldaolmak/Pictovap/issues/1) | Optional for manual testing | REST API contributors |
| Hugo CMS adapter | [#6](https://github.com/yoldaolmak/Pictovap/issues/6) | None | Filesystem and static-site contributors |

The `status: available` label means nobody has claimed the issue. The
`status: claimed` label means a contributor is actively working on it.

## Claim an Issue

Comment on the issue before writing the implementation. Include:

1. A short description of your intended approach.
2. The tests or fixtures you expect to add.
3. Any contract question that could change the implementation.

The maintainer will acknowledge the claim and switch the status label. A claim
may return to `status: available` after seven days without an update, but only
after a check-in on the issue. This avoids abandoned claims blocking another
contributor.

## Start in Five Minutes

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[test,lint]"
pytest tests/unit -q
```

Read [Writing Adapters](adapters.md) for in-tree contributions. To explore the
same contract as a standalone package:

```bash
pictovap scaffold provider example-source
pictovap scaffold cms example-cms
```

Every adapter PR must use the public helpers in `pictovap.testing`, mock all
network calls, keep credentials out of tests, and pass the complete unit suite.

## Maintainer Commitment

- Claim comments receive an initial response target of 24 hours.
- Contract and scope questions are resolved in the issue before review.
- Reviews identify required changes with file- and behavior-level detail.
- Passing code is not merged when licensing, attribution, or credential
  handling remains ambiguous.

## Checkpoints

Seven-day operational target:

- Three claimed issues.
- Two external pull requests opened.
- One pull request merged from a new external contributor.

Thirty-day operational target:

- Three new unique external contributors with merged pull requests.
- At least one provider adapter and one CMS adapter merged.
- Contributor friction found during the sprint converted into tested tooling or
  documentation fixes.

These are targets, not adoption claims. Progress is counted only from public
GitHub issue, pull-request, and merge history.
