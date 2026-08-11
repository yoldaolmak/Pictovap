# Golden Corpus Benchmark

Pictovap keeps a small set of sanitized Markdown articles in `tests/corpus/`.
Each article represents a common editorial shape: travel, recipe, news,
review, tutorial, or product guidance. The manifest records the expected
language, image-slot count, CMS placement count, and caption coverage.

Run the benchmark from a checkout with:

```bash
pictovap benchmark --corpus tests/corpus
```

Use `--format markdown` for a pull-request-friendly receipt, or `--output` to
save JSON/Markdown to a file. The command is deterministic and offline. It
uses a synthetic provider implementing the public image-source contract, then
runs the normal `create_visual_plan()` pipeline. Every case checks the same
sequence an external provider relies on:

1. Markdown article parsing and language detection
2. visual-slot creation and candidate scoring
3. provenance-pack generation
4. CMS placement and localized captions
5. strict serialized-plan validation

## Adding a case

Add a sanitized Markdown file and one manifest entry. Keep the article
credential-free and deterministic. Update only the expected values that are
intentionally changed by the parser contract, then run the benchmark and unit
tests. If a normal refactor changes a count unexpectedly, treat that as a
regression to investigate rather than updating the fixture blindly.

The corpus is a regression guard, not a quality score for editorial taste. It
does not call image providers, publish to a CMS, or claim production coverage
for a third-party integration.
