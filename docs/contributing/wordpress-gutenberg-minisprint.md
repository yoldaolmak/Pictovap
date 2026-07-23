# WordPress Gutenberg Mini Sprint

This mini sprint is for small, testable contributions around the editorial pain
Pictovap was built to address: finding the right image, preparing safe
metadata, and placing it in the right WordPress Gutenberg section.

The work below does not require a live WordPress site, credentials, paid image
APIs, or private article content. Each issue is intentionally small enough for
a first pull request.

## Claimable Work

| Issue | What it proves | Best fit |
| --- | --- | --- |
| [#40](https://github.com/yoldaolmak/Pictovap/issues/40) Add a WordPress media-library upload response fixture | Media IDs, URLs, alt text, and captions are mapped safely from a mocked WordPress response | Test-focused contributors |
| [#41](https://github.com/yoldaolmak/Pictovap/issues/41) Add a Gutenberg image-block insertion regression fixture | One image can be placed after a target heading without duplicate blocks | WordPress/Gutenberg contributors |
| [#42](https://github.com/yoldaolmak/Pictovap/issues/42) Add an editor-report example for WordPress image placement review | Editors can review image placement decisions before any CMS write | Documentation and example contributors |

All three issues use the `contribution: no-claim` label. Fork the repository,
make the smallest complete change, and open a PR directly. Do not reserve the
issue with a comment.

## First Local Loop

Use Python 3.10 or newer:

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[test,lint,typecheck]"
python -m pictovap --version
pytest tests/unit -q
```

If local setup is friction, use the
[Codespaces entry point](https://codespaces.new/yoldaolmak/Pictovap) instead.

## Boundaries

- Keep fixtures synthetic.
- Do not use a real WordPress host.
- Do not add credentials, private paths, private media URLs, or article text.
- Prefer one fixture and one behavior assertion over a broad refactor.
- Keep planning, review, upload, and publish behavior separate in wording and
  tests.

## External Validation

If you are not ready to open a PR, run Pictovap on a real non-sensitive article
and paste a safe validation report into
[issue #8](https://github.com/yoldaolmak/Pictovap/issues/8):

```bash
python -m pip install pictovap==0.7.12
pictovap plan --article path/to/article.md --output my-plan.json --report my-plan.md
pictovap feedback --plan my-plan.json --format markdown
```

The feedback command excludes article text, private paths, image URLs, and
credentials.
