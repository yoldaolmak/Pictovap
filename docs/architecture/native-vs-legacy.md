# Native vs Legacy Engine

Pictovapp operates on two engine paths. Both produce the same structured output. The difference is architecture, not behavior.

## Legacy Engine (default)

The original orchestration pipeline, living in `src/main.py` and `src/core/`.

**Strengths:**
- Battle-tested — used in production on yoldaolmak.com
- Richer semantic metadata (deeper context extraction)
- More mature quality gate behavior

**Weaknesses:**
- Monolithic — hard to extend or test in isolation
- Mixes orchestration, I/O, and business logic
- Not structured for multi-site or provider injection

**Use when:** Running production workloads, maximum metadata quality, or working with existing operator scripts.

```bash
pictova attach --site yoldaolmak --post 265713     # legacy is default
```

## Native Engine (`--engine native`)

The new engine built entirely on `src/pictova/engine/`.

**Strengths:**
- Clean separation: selector → processor → quality → metadata → publisher
- Injectable providers — easy to add new sources or destinations
- Structured output contract as first-class citizen
- Testable in isolation

**Weaknesses:**
- In active development — not all legacy behaviors ported yet
- Semantic metadata less rich than legacy path (in progress)
- Vision metadata requires `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`; falls back to deterministic metadata otherwise

**Use when:** Testing new sources, developing new profiles, or when clean output structure matters more than maximum metadata richness.

```bash
pictova attach --site yoldaolmak --post 265713 --engine native
```

## Migration Plan

The native engine is the long-term target. Migration is incremental:

| Milestone | Description | Status |
|-----------|-------------|--------|
| A | HTTP surface auth | Planned |
| B | Persisted job store | Planned |
| C | Legacy core retired into `src/pictova/engine/` | In progress |
| D | Visual memory indexer absorbed into Pictovapp repo | Planned |

No behavior is removed until the native path matches it. The legacy core remains available indefinitely until Milestone C is complete.

## Choosing an Engine

```
Is this a production publish? → legacy (default)
Is this a new source test?    → native
Is this a profile experiment? → native
Is metadata richness critical? → legacy
Is output structure critical?  → native
```
