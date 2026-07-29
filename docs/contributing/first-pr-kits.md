# First PR Kits

These kits are for contributors who want to open a useful first pull request
without asking for a claim first. Each kit is intentionally small, synthetic,
and credential-free.

Start every kit with the same local loop:

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap
python3 -m venv .venv
source .venv/bin/activate
make install
make contributor-smoke
```

If local setup is slow, use
[GitHub Codespaces](https://codespaces.new/yoldaolmak/Pictovap).

Before opening the PR, run:

```bash
make contribution-check
```

## Kit 1: WordPress media-library upload response fixture

Issue: [#40](https://github.com/yoldaolmak/Pictovap/issues/40)

Goal: prove that a mocked WordPress media-library response preserves the fields
editors need before an image is attached to a post.

Good PR shape:

- PR size: about 30-70 changed lines.
- Touch:
  - `tests/unit/test_wordpress_input.py`
  - optionally `tests/fixtures/wordpress/media-upload-response.json`
- Do not touch:
  - live WordPress configuration
  - `.env`
  - release files
  - provider adapters
- Add one mocked media upload response with:
  - `id`
  - `source_url`
  - `alt_text`
  - `caption`
- Assert that `WordPressUploader.upload_media()` returns or preserves the
  expected `media_id`, `url`, `alt_text`, and `caption` behavior.

Focused test command:

```bash
.venv/bin/python -m pytest --no-cov tests/unit/test_wordpress_input.py -q
```

Acceptance:

- No network calls.
- No real WordPress host, username, token, media URL, or private path.
- The test fails if media ID or source URL mapping regresses.

## Kit 2: Gutenberg image-block insertion regression fixture

Issue: [#41](https://github.com/yoldaolmak/Pictovap/issues/41)

Goal: prove that Pictovap can place one image after the intended Gutenberg
heading without duplicating the block on a repeated run.

Good PR shape:

- PR size: about 40-90 changed lines.
- Touch:
  - `tests/unit/test_wordpress_input.py`
  - optionally `tests/fixtures/wordpress/gutenberg-post-with-image.html`
- Do not touch:
  - live WordPress API paths
  - provider adapters
  - scoring rules
  - release files
- Use synthetic Gutenberg HTML with:
  - two H2 headings
  - one paragraph after each heading
  - one intended image placement
- Assert the generated block includes:
  - `wp-image-<media_id>`
  - image URL
  - alt text
  - caption
- Assert a second insertion does not create a duplicate `wp-image-<media_id>`
  block.

Focused test command:

```bash
.venv/bin/python -m pytest --no-cov tests/unit/test_wordpress_input.py -q
```

Acceptance:

- Fixture is synthetic and readable.
- Placement is idempotent for one target heading.
- No credentials or real WordPress requests are required.

## Kit 3: Editor-report example for WordPress image placement review

Issue: [#42](https://github.com/yoldaolmak/Pictovap/issues/42)

Goal: show what a non-technical editor reviews before approving WordPress image
placement.

Good PR shape:

- PR size: about 30-80 changed lines.
- Touch one of:
  - `examples/reports/wordpress-image-placement-review.md`
  - `docs/tutorials/wordpress-automation.md`
  - `tests/unit/test_demo.py`
- Do not touch:
  - live publishing code
  - provider adapters
  - release files
- The example should include:
  - featured image decision
  - inline Gutenberg placement decision
  - alt text
  - caption
  - source, license, and attribution fields
  - a clear note that this is review-before-publish, not a live publish claim

Focused validation:

```bash
make markdownlint
.venv/bin/python -m pytest --no-cov tests/unit/test_demo.py -q
```

Acceptance:

- The example is understandable without opening JSON.
- The text keeps planning, editor approval, and CMS publishing separate.
- It does not claim that a real WordPress site was updated.

## PR Checklist

- Keep the PR focused on one kit only.
- Mention the issue number in the PR description.
- Paste the focused test command output.
- Keep all fixtures fake and credential-free.
- If unsure, open the PR anyway and describe the question in the PR body.
