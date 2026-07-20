from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from pictovap import __version__
from pictovap.app.runtime import (
    AdapterConstructionError,
    PipelineRunner,
    parse_adapter_options,
)
from pictovap.app.cli import main


def _candidate():
    return {
        "id": "external-1",
        "filename": "external-travel.jpg",
        "provider": "external-fixture",
        "source_type": "url",
        "local_path": None,
        "source_url": "https://images.example/external-travel.jpg",
        "license": "CC0",
        "attribution": None,
        "keywords": ["minimalist", "travel", "backpack"],
        "width": 1800,
        "height": 1200,
    }


class ExternalProvider:
    def __init__(self, api_key=None, limit=8):
        self.api_key = api_key
        self.limit = limit

    def search_candidates(self, query, count):
        return [_candidate()][:min(count, self.limit)]


class EmptyExternalProvider:
    def search_candidates(self, query, count):
        return []


class ExternalCMS:
    calls = []

    def __init__(self, destination):
        self.destination = destination

    def place(self, placement):
        self.__class__.calls.append(placement)
        return {
            "placed": [item.slot_id for item in placement.placements],
            "failed": [],
            "warnings": [],
        }


@dataclass
class FakeEntryPoint:
    name: str
    value: str
    group: str
    loaded: object
    dist: object = None

    def load(self):
        return self.loaded


class FakeEntryPoints(list):
    def select(self, **params):
        return FakeEntryPoints(
            point for point in self
            if all(getattr(point, key) == value for key, value in params.items())
        )


def _install(monkeypatch, provider=ExternalProvider, cms=ExternalCMS):
    points = [
        FakeEntryPoint("external", "external:Provider", "pictovap.image_sources", provider),
        FakeEntryPoint("external", "external:CMS", "pictovap.cms", cms),
    ]
    monkeypatch.setattr("pictovap.plugins.metadata.entry_points", lambda: FakeEntryPoints(points))


def _write_plan(path):
    path.write_text(json.dumps({
        "cms_placement": {
            "article_id": "article-42",
            "adapter_target": "generic",
            "target_platform": "generic",
            "placements": [{
                "slot_id": "featured",
                "output_path": "featured.webp",
                "image_role": "featured",
                "alt_text": "A useful image",
            }],
        },
    }), encoding="utf-8")


def test_adapter_options_support_environment_and_json_scalars(monkeypatch):
    monkeypatch.setenv("EXTERNAL_TOKEN", "secret-from-environment")

    options = parse_adapter_options([
        "api_key=@EXTERNAL_TOKEN",
        "limit=3",
        "enabled=true",
        "label=plain text",
    ])

    assert options == {
        "api_key": "secret-from-environment",
        "limit": 3,
        "enabled": True,
        "label": "plain text",
    }


def test_doctor_loads_all_plugins_and_constructs_selected_adapters(monkeypatch):
    _install(monkeypatch)

    result = PipelineRunner().doctor(
        provider="external",
        cms="external",
        provider_options={"api_key": "test"},
        cms_options={"destination": "preview"},
    )

    assert result["status"] == "ready"
    assert result["pictovap"] == __version__
    assert {(item["kind"], item["load"]) for item in result["plugins"]} == {
        ("provider", "ok"),
        ("cms", "ok"),
    }
    assert result["selected"]["cms"]["option_keys"] == ["destination"]
    assert result["checks"]["write_effects"] == "not_run"


def test_doctor_reports_constructor_keys_without_secret_values(monkeypatch):
    _install(monkeypatch)

    with pytest.raises(AdapterConstructionError) as error:
        PipelineRunner().doctor(cms="external", cms_options={"wrong": "never-print-me"})

    assert "wrong" in str(error.value)
    assert "never-print-me" not in str(error.value)


def test_plan_uses_explicit_plugin_candidates(monkeypatch, tmp_path):
    _install(monkeypatch)

    result = PipelineRunner().plan(
        article="examples/articles/travel-guide.md",
        profile="examples/profiles/sample-publisher.yaml",
        provider="external",
        provider_options={"api_key": "test"},
        output=str(tmp_path / "plan.json"),
    )

    assert result["candidates_evaluated"] == 1
    assert result["runtime"]["provider"] == {"mode": "plugin", "name": "external"}
    assert all(
        scores[0]["candidate_id"] == "external-1"
        for scores in result["fit_scores"].values()
    )


def test_explicit_empty_plugin_does_not_fall_back_to_demo_candidates(monkeypatch):
    _install(monkeypatch, provider=EmptyExternalProvider)

    result = PipelineRunner().plan(
        article="examples/articles/travel-guide.md",
        provider="external",
    )

    assert result["candidates_evaluated"] == 0
    assert all(scores == [] for scores in result["fit_scores"].values())


def test_publish_dry_run_never_calls_cms_place(monkeypatch, tmp_path):
    _install(monkeypatch)
    ExternalCMS.calls.clear()
    plan = tmp_path / "plan.json"
    _write_plan(plan)

    result = PipelineRunner().publish(
        plan=str(plan),
        cms="external",
        cms_options={"destination": "preview"},
        dry_run=True,
    )

    assert result["mode"] == "dry-run"
    assert result["summary"] == {"planned": 1}
    assert result["placement"]["adapter_target"] == "external"
    assert ExternalCMS.calls == []


def test_publish_calls_cms_with_typed_placement(monkeypatch, tmp_path):
    _install(monkeypatch)
    ExternalCMS.calls.clear()
    plan = tmp_path / "plan.json"
    _write_plan(plan)

    result = PipelineRunner().publish(
        plan=str(plan),
        cms="external",
        cms_options={"destination": "live"},
    )

    assert result["status"] == "completed"
    assert result["result"]["placed"] == ["featured"]
    assert ExternalCMS.calls[0].article_id == "article-42"


def test_doctor_cli_returns_machine_readable_readiness(monkeypatch, capsys):
    _install(monkeypatch)

    exit_code = main([
        "doctor",
        "--provider", "external",
        "--provider-option", "api_key=test",
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "ready"
    assert output["selected"]["provider"]["name"] == "external"


def test_publish_cli_dry_run_is_side_effect_free(monkeypatch, tmp_path, capsys):
    _install(monkeypatch)
    ExternalCMS.calls.clear()
    plan = tmp_path / "plan.json"
    _write_plan(plan)

    exit_code = main([
        "publish",
        "--plan", str(plan),
        "--cms", "external",
        "--cms-option", "destination=preview",
        "--dry-run",
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["mode"] == "dry-run"
    assert ExternalCMS.calls == []
