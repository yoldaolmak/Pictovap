# pictovap-wikimedia

`Wikimedia` image-source adapter for Pictovap.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
pytest
pictovap plugins --kind provider
pictovap doctor --provider wikimedia
```

Run the adapter in the real planning pipeline after implementing the provider request:

```bash
pictovap plan --article article.md --provider wikimedia --output plan.json
```

Implement the provider request in `WikimediaSource.search_candidates`,
mock all HTTP calls in tests, and preserve Wikimedia attribution and license
fields in every returned candidate. Wikimedia Commons does not require an API
key for this adapter.
