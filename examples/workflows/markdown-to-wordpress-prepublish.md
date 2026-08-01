# Markdown to WordPress Pre-Publish Image Workflow

This example shows where Pictovap fits when a publisher already uses a
Markdown-to-WordPress importer.

## Goal

Keep the importer responsible for WordPress authentication, post creation, and
media upload. Use Pictovap before that step to prepare an editor-approved image
plan.

## Step 1: Prepare the article

```text
posts/example.md
profiles/publisher.yaml
```

The article can come from a Markdown editor, AI draft tool, static-site
generator, or CMS export.

## Step 2: Generate a Pictovap plan

```bash
pictovap plan \
  --article posts/example.md \
  --profile profiles/publisher.yaml \
  --output artifacts/pictovap-plan.json \
  --report artifacts/pictovap-report.md
```

The JSON file is for automation. The Markdown report is for editor approval.

## Step 3: Review before publishing

The editor checks:

- whether each visual slot belongs under the suggested heading;
- whether the selected image fits the surrounding section;
- whether alt text and caption are acceptable;
- whether license, attribution, and source data are present;
- whether any candidate marked `needs_review` should be replaced.

No live WordPress write is required for this review.

## Step 4: Hand off to the WordPress importer

After approval, the downstream importer or CMS adapter can publish the article
and media using its own credentials and safety model.

Pictovap should not own the importer credentials unless a CMS adapter is
explicitly configured and validated:

```bash
pictovap adapter check --kind cms --name wordpress
pictovap publish --plan artifacts/pictovap-plan.json --cms wordpress --dry-run
```

Use dry-run output before any real CMS write.

## Integration Boundary

```text
Markdown authoring
  -> Pictovap visual plan
  -> editor approval
  -> Markdown-to-WordPress importer
  -> WordPress draft or publish action
```

This keeps Pictovap focused on image intent, provenance, and placement
reasoning while the importer remains responsible for WordPress transport.

## Generate a PR Packet for an Importer

If you maintain or contribute to a Markdown-to-WordPress importer, generate a
copyable integration packet:

```bash
pictovap ecosystem match \
  --tool markdown-to-wordpress \
  --project-name "Your Importer" \
  --format markdown \
  --output pictovap-integration.md
```

Review the anti-spam checklist in the generated file before opening an
ecosystem PR.
