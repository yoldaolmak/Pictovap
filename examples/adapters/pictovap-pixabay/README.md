# pictovap-pixabay

`Pixabay` image-source adapter for Pictovap.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
pytest
pictovap plugins --kind provider
pictovap doctor --provider pixabay
pictovap adapter check --kind provider --name pixabay
```

Run the adapter in the real planning pipeline:

```bash
export PIXABAY_API_KEY="..."
pictovap plan --article article.md --provider pixabay \
  --provider-option api_key=@PIXABAY_API_KEY --output plan.json
```

The package maps Pixabay hits to the Pictovap candidate contract, preserves the
provider attribution and license fields, and keeps all HTTP calls mocked in
the test suite. Missing credentials and API failures remain safe empty-result
paths.
