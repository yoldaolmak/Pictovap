# Building Third-Party Adapter Plugins

Pictovap adapters can ship as independent Python distributions. A plugin does
not need a change in Pictovap core: installation makes it discoverable through
a standard Python entry point.

This is the preferred route when an integration has its own release cadence or
provider-specific dependencies. In-tree adapters remain appropriate for small,
widely useful integrations maintained with the core project.

## Generate a Working Package

Create a provider plugin:

```bash
pictovap scaffold provider wikimedia
cd pictovap-wikimedia
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
pytest
```

Create a CMS plugin:

```bash
pictovap scaffold cms hugo
```

`--output` is a parent directory, not the package directory itself. For
example, this creates `adapters/pictovap-hugo`:

```bash
pictovap scaffold cms hugo --output adapters
cd adapters/pictovap-hugo
```

The generated project includes a `src/` package, entry-point metadata, a
contract test, a README, and an isolated `.gitignore`. Existing scaffold files
are never overwritten unless `--force` is passed. Package metadata defaults to
MIT, matching Pictovap; change it before publishing if the plugin uses another
OSI-approved license.

## Entry-Point Groups

Provider packages register an adapter class under `pictovap.image_sources`:

```toml
[project.entry-points."pictovap.image_sources"]
wikimedia = "pictovap_wikimedia:WikimediaSource"
```

CMS packages use `pictovap.cms`:

```toml
[project.entry-points."pictovap.cms"]
hugo = "pictovap_hugo:HugoAdapter"
```

Report-renderer packages use `pictovap.report_renderers`:

```toml
[project.entry-points."pictovap.report_renderers"]
html-review = "pictovap_html_review:HTMLReviewRenderer"
```

Entry points must expose a class implementing `ImageSourceAdapter`,
`CMSAdapter`, or `ReportRenderer` for their selected group. Pictovap rejects
duplicate names and classes that do not satisfy the selected protocol.

Inspect installed plugins with:

```bash
pictovap plugins
pictovap plugins --kind provider
pictovap plugins --kind cms
pictovap plugins --kind renderer
```

The output is JSON so CI and other tools can consume it.

For complete provider references, see
[`examples/adapters/pictovap-pixabay`](../../examples/adapters/pictovap-pixabay/)
and [`examples/adapters/pictovap-wikimedia`](../../examples/adapters/pictovap-wikimedia/).
They include real response mapping and mocked contract tests while the matching
in-tree adapter issues remain available for contribution.

Validate one installed adapter without writes:

```bash
pictovap adapter check --kind provider --name wikimedia
pictovap adapter check --kind renderer --name html-review
```

Provider result fields are checked only when `--exercise` is explicitly passed;
that avoids accidental provider traffic during a normal conformance check.

## From Installation to a Real Workflow

Discovery is only the first gate. Check constructor configuration without CMS
writes, then run the provider through the real planning pipeline:

```bash
pictovap plan \
  --article article.md \
  --provider wikimedia \
  --output plan.json \
  --report report.md
```

Pictovap calls `search_candidates`, validates every candidate, and sends those
exact records into Fit Score. Empty results stay empty for an explicitly named
plugin; mock candidates are never substituted.

For a CMS plugin, inspect the operations before allowing writes:

```bash
export HUGO_OUTPUT_DIR="/srv/site/content"
pictovap doctor --cms hugo --cms-option output_directory=@HUGO_OUTPUT_DIR
pictovap publish --plan plan.json --cms hugo --dry-run \
  --cms-option output_directory=@HUGO_OUTPUT_DIR
```

Once the preview is correct, remove `--dry-run`. Pictovap reconstructs the
typed `CMSPlacement`, calls the third-party adapter once, and validates its
complete result contract.

Option values use JSON scalar decoding (`limit=3`, `enabled=true`). Use
`key=@ENV_VAR` for credentials and sensitive paths; diagnostics contain option
names, never their values.

## Contract Test Kit

Third-party packages should test their public boundary with the helpers shipped
in `pictovap.testing`:

```python
from pictovap_wikimedia import WikimediaSource
from pictovap.testing import assert_image_source_contract


def test_contract(fake_client):
    adapter = WikimediaSource()
    fake_client.respond_with_fixture("tests/fixtures/search.json")
    candidates = assert_image_source_contract(adapter, query="harbor", count=3)
    assert candidates
```

For a CMS adapter:

```python
from pictovap_hugo import HugoAdapter
from pictovap.testing import assert_cms_adapter_contract


def test_contract(tmp_path):
    adapter = HugoAdapter(output_directory=tmp_path)
    result = assert_cms_adapter_contract(adapter)
    assert not result["failed"]
```

The caller must mock network and filesystem effects. The helpers validate the
runtime protocol, candidate field types, result shape, and requested candidate
limit. They do not make external requests themselves.

## Release Checklist

- Keep credentials in environment variables or explicit constructor arguments.
- Mock all provider and CMS calls in tests.
- Run the contract helper against both success and failure fixtures.
- Declare `pictovap>=0.6.0` in the plugin package.
- Verify `doctor`, a real provider-backed `plan`, and CMS `publish --dry-run`.
- Use a unique entry-point name and a `pictovap-<adapter>` distribution name.
- Document license and attribution behavior for image sources.
- Document idempotency and rollback limits for CMS targets.

Open a Pictovap discussion or issue when the plugin needs a core contract
change. Do not work around the contract with undocumented output fields.
