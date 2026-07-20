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

Run the adapter in the real planning pipeline:

```bash
export WIKIMEDIA_API_KEY="..."
pictovap plan --article article.md --provider wikimedia \
  --provider-option api_key=@WIKIMEDIA_API_KEY --output plan.json
```

Implement the provider request in `WikimediaSource.search_candidates`,
mock all HTTP calls in tests, and preserve the credential-free empty-result path.
