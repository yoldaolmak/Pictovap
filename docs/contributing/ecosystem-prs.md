# Ecosystem Pull Requests

Pictovap grows best through useful adjacent contributions, not link dropping.
This guide defines when an external pull request is appropriate.

## The Test

Before opening a PR to another repository, answer yes to all five questions:

1. Is the repository active enough that a maintainer might reasonably review
   the PR?
2. Is the repository about WordPress, Gutenberg, Markdown publishing, CMS
   automation, media upload, image sourcing, or editorial workflow?
3. Does the change improve the target repository's documentation or examples
   even if the Pictovap link is ignored?
4. Is Pictovap mentioned as a companion workflow, not as a replacement?
5. Is the text specific to the target project rather than copied from another
   PR?

If any answer is no, do not open the PR.

## Preferred PR Shapes

Good ecosystem PRs are small and concrete:

- a "related tools" section in a curated list;
- a "pre-publish image planning" note in a Markdown-to-WordPress tool;
- a "visual review boundary" note in an AI draft or CMS automation project;
- a short example showing where an editor report fits before publish;
- a documentation correction discovered while testing the target project.

Avoid large rewrites, unsolicited architecture changes, or PRs whose only
change is a bare Pictovap link.

## Natural Pictovap Positioning

Use this shape when it fits the target project:

```text
<Target project> handles <its responsibility>.
If the workflow also needs image selection, attribution, alt/caption review,
or Gutenberg placement planning before publishing, Pictovap can be used as a
companion pre-publish workflow.
```

Examples:

- Markdown importer: "Keep this tool as the import layer; run Pictovap before
  import when editors need a visual plan."
- AI draft plugin: "Generate the draft here; run Pictovap after the draft for
  image sourcing and review."
- Media uploader: "Upload already chosen media here; use Pictovap before upload
  to decide which media belongs where."

## Cadence

A healthy cadence is a few high-quality external PRs per week, not a burst of
identical PRs. Track:

- opened PRs;
- merged PRs;
- maintainer replies;
- rejected or ignored patterns;
- any visitors or contributors who come back to Pictovap.

If maintainers start rejecting the same wording, stop using that pattern and
write a more useful target-specific contribution.

## Review Checklist

Before submitting:

- The PR title is about the target repository, not Pictovap.
- The body explains why the target project's users benefit.
- The change is docs-only unless a real bug or test was found.
- The Pictovap link appears once.
- The text avoids SEO, traffic, or "complete automation" claims.
- The target repository's language and tone are respected.
