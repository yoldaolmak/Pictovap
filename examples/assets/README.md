# examples/assets

This directory is referenced by the Pictovap local demo (`make demo` / `python -m pictova.demo`).

## Mock Asset References

The demo uses mock image candidate metadata. The following filenames are referenced
in `src/pictova/demo.py` as `local_path` values:

| Filename | Keywords | License |
|---|---|---|
| `minimal-backpack.jpg` | backpack, travel, minimalist, packing | CC0 |
| `forest-path.jpg` | forest, nature, path, serenity, trees | CC0 |
| `blurry-phone.jpg` | phone, blurry, travel | owned |

These files are **not committed** to the repository. The demo does not read their
pixel content — it only evaluates their metadata (dimensions, license, keywords)
using the mock candidate dictionaries defined in `demo.py`.

The demo's scoring is fully deterministic and runs without any actual image files.

## Adding Real Assets

To test with real local images:

1. Place your image files here.
2. Add entries to the `MOCK_CANDIDATES` list in `src/pictova/demo.py` with the correct
   `local_path`, `license`, `keywords`, `width`, and `height` values.
3. Re-run `make demo`.

No credentials are required for local file sources.
