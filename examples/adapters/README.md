# Runnable Adapter Examples

Working skeletons for the two adapter types. Both run with **zero
credentials and zero network access** — the fastest way to understand the
contracts before writing a real adapter.

```bash
pip install pictovap

python examples/adapters/custom_image_source.py
python examples/adapters/custom_cms_adapter.py
```

| Example | Contract | What it does |
|---------|----------|--------------|
| [`custom_image_source.py`](custom_image_source.py) | `ImageSourceAdapter` | Serves candidates from a JSON manifest; shows the required candidate shape, graceful degradation, and the runtime `isinstance` contract check |
| [`custom_cms_adapter.py`](custom_cms_adapter.py) | `CMSAdapter` | Runs the real planner on the packaged sample article, then executes the resulting `CMSPlacement` by writing a Markdown file — a stand-in for a static-site CMS |

## From skeleton to real adapter

1. Read [docs/contributing/adapters.md](../../docs/contributing/adapters.md)
   for the full checklist (file locations, credential rules, test
   requirements).
2. Reference implementations: `src/pictovap/providers/openverse.py`
   (key-free image source), `src/pictovap/providers/pexels.py`
   (key-gated image source), `src/pictovap/publishers/ghost.py` and
   `src/pictovap/publishers/strapi.py` (API-backed CMS adapters).
3. Adapters wanted right now: see the
   [open issues](https://github.com/yoldaolmak/Pictovap/issues) —
   Pixabay, Wikimedia Commons, and Hugo are up for grabs.
4. For a separately installable renderer package, see the complete
   [`external-renderer-package`](../external-renderer-package/README.md)
   example, including entry-point discovery, contract testing, and CLI use.
