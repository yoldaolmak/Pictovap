from __future__ import annotations

from pictovap.conformance import AdapterCheckError, check_adapter


class FixtureProvider:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def search_candidates(self, query, count):
        return [{
            "id": "fixture", "filename": "fixture.jpg", "provider": "fixture",
            "source_type": "url", "local_path": None, "source_url": "https://example.test/fixture.jpg",
            "license": "cc0", "attribution": None, "keywords": [query], "width": 1200, "height": 800,
        }][:count]


class LeakingProvider(FixtureProvider):
    def __init__(self, api_key: str | None = None):
        print(api_key)
        super().__init__(api_key)


class FixtureRenderer:
    def render(self, plan):
        return "<html><body>Fixture report</body></html>"


def test_provider_check_exercises_contract_without_cms_writes(monkeypatch):
    monkeypatch.setattr("pictovap.conformance.construct_plugin", lambda *args: FixtureProvider())

    report = check_adapter(kind="provider", name="fixture", exercise=True)

    assert report["status"] == "passed"
    assert report["checks"]["source_adapter_contract"]["status"] == "passed"
    assert report["checks"]["provenance_fields"]["status"] == "passed"
    assert report["checks"]["dry_run"]["status"] == "passed"


def test_check_detects_constructor_credential_leakage(monkeypatch):
    monkeypatch.setattr(
        "pictovap.conformance.construct_plugin", lambda *args: LeakingProvider("secret-value")
    )

    report = check_adapter(kind="provider", name="fixture", options={"api_key": "secret-value"})

    assert report["status"] == "failed"
    assert report["checks"]["credential_leakage"]["status"] == "failed"


def test_renderer_check_renders_without_writes(monkeypatch):
    monkeypatch.setattr("pictovap.conformance.construct_plugin", lambda *args: FixtureRenderer())

    report = check_adapter(kind="renderer", name="fixture")

    assert report["status"] == "passed"
    assert report["checks"]["report_renderer_contract"]["status"] == "passed"
    assert report["checks"]["render_output"]["status"] == "passed"


def test_check_rejects_unsafe_exercise_for_cms():
    try:
        check_adapter(kind="cms", name="fixture", exercise=True)
    except AdapterCheckError as error:
        assert "provider" in str(error)
    else:
        raise AssertionError("Expected an unsafe CMS exercise to fail")
