# Ecosystem Integrations

Pictovap is most useful when it sits between content creation and CMS
publishing. It does not need to replace Markdown editors, AI draft tools,
static-site generators, WordPress importers, or media upload scripts. It can
prepare the missing visual-finishing layer those tools usually leave to a
human editor.

## Where Pictovap Fits

Use Pictovap when another tool already creates or imports article content, but
does not answer the editorial image questions:

- Which section needs a visual?
- Which candidate image actually fits that section?
- Is the image license and attribution recorded?
- Are alt text and captions ready for review?
- Where should the image be placed in WordPress, Gutenberg, or another CMS?

The boundary is intentionally narrow:

```text
Draft or Markdown article
  -> Pictovap visual plan and editor report
  -> CMS import, media upload, or publish workflow
```

Pictovap produces reviewable artifacts before a live publishing tool writes to
a site.

## Generate an Integration Packet

Use the CLI to create a target-specific integration packet before opening an
external PR:

```bash
pictovap ecosystem match \
  --tool markdown-to-wordpress \
  --project-name md2wp \
  --repository-url https://github.com/example/md2wp \
  --format markdown \
  --output pictovap-integration.md
```

The generated file contains a README section, PR body, workflow commands, and
anti-spam checklist. This keeps ecosystem contributions useful to the target
repository instead of turning them into link drops.

Supported tool kinds:

```bash
pictovap ecosystem explain --format markdown
```

## Compatible Project Types

| Project type | What it usually owns | What Pictovap can add |
| --- | --- | --- |
| Markdown-to-WordPress importers | Convert Markdown to WordPress posts or WXR | Pre-import image placement plan, alt text, captions, provenance |
| WordPress AI draft tools | Generate draft article content | Post-draft visual brief, image sourcing, editor review report |
| Gutenberg block tools | Render or modify block markup | Placement intent, source/attribution data, review-before-publish workflow |
| Static-site migration tools | Move Markdown or generated HTML into a CMS | CMS-neutral visual plan before migration |
| Media upload scripts | Upload referenced local images | Candidate selection, license checks, and placement reasoning before upload |

Pictovap should not be presented as a replacement for those projects. It is a
companion workflow for the visual-finishing step.

## Markdown-to-WordPress Workflow

For a Markdown publisher, the safest chain is:

```bash
pictovap plan \
  --article posts/example.md \
  --profile publisher.yaml \
  --output pictovap-plan.json \
  --report pictovap-report.md
```

An editor reviews `pictovap-report.md` first. After approval, a downstream
WordPress importer can use the article and selected media in its own
publish/import step.

This keeps responsibilities clean:

1. The Markdown tool owns article conversion and WordPress authentication.
2. Pictovap owns image intent, candidate scoring, provenance, and editor
   review.
3. A CMS adapter or importer owns the final write.

## AI Draft Workflow

For AI-assisted WordPress drafting, use Pictovap after the draft exists:

```text
Topic or source URLs
  -> AI draft tool
  -> Markdown or draft export
  -> Pictovap visual plan
  -> editor approval
  -> CMS write
```

This avoids mixing draft generation with image-license and placement decisions.
It also gives editors a separate artifact for reviewing visual choices.

## CMS Adapter Workflow

If a project wants to execute Pictovap's placement plan directly, write or
install a CMS adapter and validate it before any live write:

```bash
pictovap adapter check --kind cms --name your-cms
pictovap publish --plan pictovap-plan.json --cms your-cms --dry-run
```

The dry run should show what would be placed without changing a live site.

## Good Integration Language

Use specific boundary language when referencing Pictovap from another project:

> For image selection, attribution, alt/caption review, and Gutenberg placement
> planning before the final WordPress import, Pictovap can be used as a
> companion pre-publish workflow.

Avoid vague promotional language:

- "AI image automation"
- "best WordPress image tool"
- "complete publishing automation"
- "traffic or SEO guarantee"

Those claims are either too broad or not what Pictovap does.

## Maintainer Rule for External PRs

When adding Pictovap to another open-source project, the target repository must
benefit even if no one clicks the Pictovap link. Good external PRs usually do
one of these:

- clarify the target project's publishing boundary;
- add a related-tools section where Pictovap is one relevant entry;
- document a safe pre-publish image workflow;
- improve examples around WordPress, Gutenberg, Markdown, or CMS media work.

Do not paste the same paragraph into many repositories. Each contribution
should be written for the target project's actual workflow.
