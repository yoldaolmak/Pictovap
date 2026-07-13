from __future__ import annotations

from dataclasses import dataclass

import pytest

from pictovap.plugins import (
    DuplicatePluginError,
    PluginContractError,
    PluginLoadError,
    PluginNotFoundError,
    iter_plugins,
    load_plugin,
)


class FakeProvider:
    def search_candidates(self, query, count):
        return []


class FakeCMS:
    def place(self, placement):
        return {"placed": [], "failed": [], "warnings": []}


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
            entry_point
            for entry_point in self
            if all(getattr(entry_point, key) == value for key, value in params.items())
        )


def _install_entry_points(monkeypatch, *entry_points):
    monkeypatch.setattr("pictovap.plugins.metadata.entry_points", lambda: FakeEntryPoints(entry_points))


def test_iter_plugins_discovers_both_contract_groups(monkeypatch):
    _install_entry_points(
        monkeypatch,
        FakeEntryPoint("fixture", "fixture:Provider", "pictovap.image_sources", FakeProvider),
        FakeEntryPoint("fixture", "fixture:CMS", "pictovap.cms", FakeCMS),
    )

    plugins = iter_plugins()

    assert [(plugin.kind, plugin.name) for plugin in plugins] == [
        ("cms", "fixture"),
        ("provider", "fixture"),
    ]
    assert plugins[0].to_dict()["entry_point"] == "fixture:CMS"


def test_load_plugin_returns_protocol_conforming_class(monkeypatch):
    _install_entry_points(
        monkeypatch,
        FakeEntryPoint("fixture", "fixture:Provider", "pictovap.image_sources", FakeProvider),
    )

    assert load_plugin("provider", "fixture") is FakeProvider


def test_load_plugin_rejects_wrong_contract(monkeypatch):
    _install_entry_points(
        monkeypatch,
        FakeEntryPoint("broken", "fixture:Broken", "pictovap.cms", object),
    )

    with pytest.raises(PluginContractError, match="CMSAdapter"):
        load_plugin("cms", "broken")


def test_missing_plugin_has_actionable_error(monkeypatch):
    _install_entry_points(monkeypatch)

    with pytest.raises(PluginNotFoundError, match="pictovap.image_sources"):
        load_plugin("provider", "missing")


def test_duplicate_names_fail_closed(monkeypatch):
    _install_entry_points(
        monkeypatch,
        FakeEntryPoint("same", "one:Provider", "pictovap.image_sources", FakeProvider),
        FakeEntryPoint("same", "two:Provider", "pictovap.image_sources", FakeProvider),
    )

    with pytest.raises(DuplicatePluginError, match="Multiple plugins"):
        iter_plugins("provider")


def test_load_failure_names_the_broken_entry_point(monkeypatch):
    entry_point = FakeEntryPoint(
        "broken", "missing.module:Adapter", "pictovap.cms", FakeCMS,
    )

    def fail_to_load():
        raise ImportError("missing dependency")

    entry_point.load = fail_to_load
    _install_entry_points(monkeypatch, entry_point)

    with pytest.raises(PluginLoadError, match="missing.module:Adapter"):
        load_plugin("cms", "broken")
