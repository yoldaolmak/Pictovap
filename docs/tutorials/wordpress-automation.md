# Prepare WordPress Gutenberg Image Plans with Pictovap

WordPress publishers repeatedly solve the same visual-editor problem: decide
where images belong, find candidates that fit the surrounding content, keep
license and attribution data, and give an editor a reviewable result. Pictovap
turns that work into a deterministic visual plan. It is CMS-neutral; the
WordPress-specific boundary is the input and placement adapter.

This tutorial covers the supported, write-free workflow. It creates a plan and
an editor report without changing a WordPress post.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install pictovap
```

## Create a publisher profile

Profiles use the versioned Pictovap schema. Start with the checked-in example
and adapt the fields that describe your publication:

```bash
cp examples/profiles/sample-publisher.yaml publisher.yaml
```

At minimum, a profile contains `schema_version`, `profile_id`, and
`brand_name`:

```yaml
schema_version: 1
profile_id: my-wordpress-site
brand_name: My WordPress Site
cms_type: wordpress
language: en
image_sources:
  - openverse
caption_rules:
  include_attribution: true
```

## Create a plan from Markdown

Use this path when the article is maintained in a repository or a CMS export:

```bash
pictovap plan \
  --article draft-post.md \
  --profile publisher.yaml \
  --output plan.json \
  --report report.md
```

The JSON plan contains the visual brief, scored candidate images, provenance,
and placement instructions. The Markdown report is the editor-facing review
surface.

## Create a plan from an existing WordPress post

Pictovap can read a Gutenberg post through the WordPress REST API. It does not
write, upload media, or publish during this command.

```bash
export WP_URL="https://yourblog.example"
export WP_USER="editor"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"

pictovap plan \
  --wordpress-post 42 \
  --output plan.json \
  --report report.md
```

For a named site, use `--wordpress-site publisher` and the corresponding
`PUBLISHER_URL`, `PUBLISHER_USER`, and `PUBLISHER_APP_PASSWORD` variables.

## Review the result

```bash
pictovap report --plan plan.json --output report.md
```

Check the image role, heading placement, source URL, license, attribution, and
alt text before a publisher or CMS adapter performs any write.

## Use the GitHub Action

The repository also exposes a small Action for planning one Markdown file per
run. It does not upload media or modify WordPress:

```yaml
name: Visual plan

on:
  pull_request:
    paths: ["posts/**/*.md"]

jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: yoldaolmak/Pictovap@v0.7.12
        with:
          article: posts/example.md
          profile: publisher.yaml
          output: artifacts/pictovap-plan.json
          report: artifacts/pictovap-report.md
```

For multiple articles, invoke the Action once per file from a matrix. A glob
such as `posts/*.md` is not a valid `article` value.

## Extending the write step

Uploading media and placing Gutenberg blocks is deliberately an adapter
boundary. Implement or install a `CMSAdapter`, validate it with
`pictovap adapter check --kind cms`, and only then call it with a plan. This
keeps the planning step safe and lets contributors add CMS integrations without
changing Pictovap core.
