# Contributing

## Naming Convention

All code and documentation must use **Pictova** as the product name, `pictova` as the CLI command, and `src.pictova` as the Python package root. See [Brand & Naming Doctrine](docs/architecture/naming.md).

## Branch and Commit

- Branch from `main`
- Commit messages: `type: short description` (feat, fix, docs, refactor, test, ops)
- Every completed change must be committed and pushed — unpushed work is not done

## Adding a Feature

1. Update `QWEN_STATUS.md` — wait, that file is gone. Instead: update `CHANGELOG.md` under `[Unreleased]`
2. Write or update tests in `tests/`
3. Run `python3 -m pytest -q` — all must pass
4. Update relevant `docs/` page

## Adding an Image Source

1. Implement `src/pictova/providers/mysource.py` — see [Adding Sources](docs/guides/adding-sources.md)
2. Register in `src/pictova/config.py`
3. Add to a site profile's `source_priority`
4. Add a section to `docs/guides/adding-sources.md` and `docs/concepts/sources.md`

## Architecture Rules

- App layer (`src/pictova/app/`) contains no business logic
- Engine layer (`src/pictova/engine/`) performs no direct I/O — use injected providers
- Do not add new code to `src/core/` or `src/main.py` — migrate into `src/pictova/engine/` instead
- Do not delete legacy modules if anything still imports them

## Testing

```bash
python3 -m pytest -q              # run all tests
python3 -m pytest tests/unit/     # unit only
python3 -m pytest tests/integration/  # integration only
```

Integration tests require no WordPress credentials — they test the CLI contract with structured failure responses.

## Documentation

- All docs are in English
- Every new feature needs at least one updated doc page
- Concepts = what/why; Guides = how; Reference = complete spec; Architecture = design decisions
