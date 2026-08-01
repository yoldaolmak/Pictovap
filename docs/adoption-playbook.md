# External Adoption Playbook

Welcome to Pictovap! This playbook is designed to help you quickly understand, run, and test Pictovap in your own environment without needing API keys, cloud accounts, or complex setup.

## 1. Who Should Try Pictovap First

Pictovap is an early-stage open-source infrastructure project. You are an ideal early tester if you are:
- An independent publisher
- A WordPress blogger
- A travel or recipe publisher
- A local guide publisher
- Part of a small editorial team seeking to automate visual finishing

*Note: Pictovap does not currently provide a consumer-friendly UI. It is for publishers comfortable running Python scripts or integrating APIs.*

## 2. What You Can Test in 10 Minutes

In just 10 minutes, without any credentials, you can:
- Install the current PyPI package.
- Run the core pipeline (Visual Brief → Fit Score → Provenance Pack → CMS Placement).
- Test how Pictovap evaluates images against a mock dataset.
- Run a custom Markdown article through the engine.
- Generate a safe Markdown validation report without sharing article text,
  private paths, image URLs, or credentials.

## 3. Run the Default Demo

Set up a virtual environment, install the current release from PyPI, and run
the standard credential-free demo:

```bash
python3 --version  # Python 3.10 or newer
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pictovap

pictovap demo
```

This runs the engine against bundled sample content using deterministic mock
image candidates. It does not read `.env`, call image APIs, or contact a CMS.

## 4. Try Your Own Markdown Article

You can test Pictovap against your own content:

```bash
pictovap plan \
  --article path/to/your/article.md \
  --output my-plan.json \
  --report my-plan.md
pictovap feedback --plan my-plan.json --format markdown
```

It will parse your article, identify sections, evaluate deterministic mock
candidates for placement, write a JSON plan, write a Markdown editor report,
and print a GitHub-ready validation summary.

## 5. Create a Publisher Profile

Publisher profiles tell Pictovap about your site's tone and requirements.
For source checkouts, try creating your own profile based on
`examples/profiles/sample-publisher.yaml`. Copy the file, edit the tone rules,
and pass it to `pictovap plan` using the `--profile` flag.

## 6. Review the Outputs

Open the generated JSON plan and Markdown report. Look for the four primitives:
- `visual_brief`: What the engine thinks your article needs.
- `fit_scores`: How candidate images were ranked.
- `provenance_packs`: The selected images and their audit trail.
- `cms_placement`: The final placement instructions.

The feedback command prints only safe counts plus Python and coarse OS
metadata. It excludes article text, private paths, image URLs, profile names,
and credentials.

## 7. Report a Useful Validation Result

Paste the generated feedback Markdown into a
[new external validation issue](https://github.com/yoldaolmak/Pictovap/issues/new?template=external_validation.md).
Good reports include success, confusing output, or failures:

- The `visual_brief` matched or missed the article structure.
- The report was or was not useful for editorial review.
- The command crashed when parsing a specific Markdown element.
- The generated OS/Python metadata and traceback if it failed.

## 8. Contribute a Sample Article/Profile

Help us make Pictovap more publisher-agnostic! If you have a unique article format (e.g., a heavily structured recipe), consider opening a Pull Request to add it to `examples/articles/` along with a corresponding profile in `examples/profiles/`.

## 9. Request an Adapter

Pictovap is built around adapters. If you use a specific image source (like Openverse) or CMS (like Ghost or Strapi), open an "Adapter Request" issue. Check our existing requests before submitting.

## 10. Try a Standalone Plugin

The repository includes complete, independently installable provider references
with mocked contract tests:

- [`pictovap-pixabay`](../examples/adapters/pictovap-pixabay/)
- [`pictovap-wikimedia`](../examples/adapters/pictovap-wikimedia/)
- [`pictovap-external-html-review`](../examples/external-renderer-package/)

These packages demonstrate entry-point discovery and the adapter conformance
check without changing Pictovap core. Use them as a starting point for a
downstream package with its own release cadence.

## 11. Connect Pictovap to an Existing Publishing Tool

If you already use a Markdown-to-WordPress importer, AI draft plugin, static
site migration script, or media uploader, do not replace it. Run Pictovap before
that tool to prepare a visual plan and editor report.

See [Ecosystem Integrations](ecosystem-integrations.md) for the supported
boundary and
[Markdown to WordPress Pre-Publish Image Workflow](../examples/workflows/markdown-to-wordpress-prepublish.md)
for a copyable sequence.

## 12. Current Limitations

- The credential-free demo relies on mock assets and deterministic scoring, not live APIs.
- Real API runs (with external model providers) require configuration not covered in this quick playbook.
- WordPress is the most production-hardened CMS path. Ghost, Strapi, and Hugo
  reference paths exist, but broader downstream validation is still needed.
- Pictovap does not claim broad downstream adoption yet. Six external PRs from
  five contributors have been merged; current adapter and Gutenberg issues are
  the most direct way to add another real contribution.
