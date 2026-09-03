# Image Sources

Pictovap can draw candidate images from multiple source types simultaneously or selectively.
Each source is an adapter that implements the standard candidate interface and returns
metadata-enriched candidates for the Fit Score stage.

## Source Types

### Local Directory

Reads image files from a local directory. No credentials required.

```
PICTOVAP_LOCAL_IMAGE_DIR=/path/to/images  # environment variable
```

This is the only source used by the local demo. No API key needed.

### Unsplash (Free API)

Queries the Unsplash API for royalty-free images matching the Visual Brief topic.

```
UNSPLASH_ACCESS_KEY=your_key_here  # .env
```

### DepositPhotos (Licensed Stock)

Queries DepositPhotos for licensed stock images.

```
DEPOSIT_API_KEY=your_key_here  # .env
```

## How Sources Are Combined

When multiple sources are configured in the publisher profile:

1. Each enabled source is queried independently.
2. All candidates are scored using the Fit Score engine.
3. Candidates are ranked across sources by final score.
4. Hard rejections (resolution, license) are applied before ranking.
5. The top candidates pass to the Provenance Pack stage.

You can restrict to a single source by configuring `image_sources` in the publisher profile.

## Adding a New Source

Sources are implemented as adapters under `src/pictovap/providers/`. A new source needs:

1. A file in `src/pictovap/providers/` implementing the candidate dict interface.
2. Registration in the profile system.
3. A credential key in `.env.example` (if credentials are needed).
4. Unit tests with mocked external calls.

See [Image Source Adapters](../adapters/image-sources.md) for the full interface contract
and [Writing Adapters](../contributing/adapters.md) for the contribution guide.

## Credential Isolation

All source credentials must come from environment variables. The local demo runs with
no `.env` file and no credentials. Sources that require credentials are simply not queried
when their environment variable is unset.

## Source Evidence in a Plan

A source that returns nothing and a source that could not run at all are not the
same fact, and a plan that shows only candidates cannot tell them apart. Every
plan therefore carries one record per configured source under
`runtime.sources`:

| State | Meaning |
| --- | --- |
| `observed` | The adapter ran. `candidates` is what it actually returned, including zero. |
| `not_evaluable` | No conclusion was possible. `reason` is `adapter_error` or `unimplemented_source`. |
| `unknown` | The source was not queried, so its result is not known. `reason` says why. |

```json
{
  "sources": [
    {"source": "local", "state": "observed", "candidates": 3},
    {"source": "unsplash", "state": "not_evaluable", "candidates": 0,
     "reason": "adapter_error", "error_type": "HTTPError"},
    {"source": "pixabay", "state": "not_evaluable", "candidates": 0,
     "reason": "unimplemented_source"}
  ]
}
```

Only the exception class is recorded, never its message: an adapter's error text
can carry a request URL with an embedded API key, and this record is serialized
into a plan that gets committed, shared, and pasted into issues.

Reading these states in the canonical way matters. `unknown` does not mean a
source failed, and `not_evaluable` does not mean a source found nothing. Neither
one licenses a claim that an article's visual coverage was fully assessed.

## Compatibility Note

Product name: Pictovap.
The Python package and CLI are `pictovap`.
