"""Discovery and loading for third-party Pictovap adapter plugins."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
from typing import Dict, Iterable, Literal, Type

from pictovap.core.adapters import CMSAdapter, ImageSourceAdapter

AdapterKind = Literal["provider", "cms"]

ENTRY_POINT_GROUPS: Dict[AdapterKind, str] = {
    "provider": "pictovap.image_sources",
    "cms": "pictovap.cms",
}


class PluginError(RuntimeError):
    """Base class for plugin discovery and loading failures."""


class DuplicatePluginError(PluginError):
    """Raised when two distributions register the same adapter name."""


class PluginNotFoundError(PluginError):
    """Raised when a requested adapter is not installed."""


class PluginContractError(PluginError):
    """Raised when an entry point does not expose the required adapter class."""


class PluginLoadError(PluginError):
    """Raised when an installed entry point cannot be imported."""


def _entry_points_for(group: str) -> Iterable[metadata.EntryPoint]:
    discovered = metadata.entry_points()
    if hasattr(discovered, "select"):
        return discovered.select(group=group)
    return discovered.get(group, ())  # pragma: no cover - Python < 3.10 compatibility


@dataclass(frozen=True)
class AdapterPlugin:
    """Metadata and lazy loader for one installed adapter plugin."""

    name: str
    kind: AdapterKind
    value: str
    distribution: str | None
    _entry_point: metadata.EntryPoint

    def load(self) -> Type[object]:
        """Load the registered class and enforce its adapter protocol."""
        try:
            adapter_class = self._entry_point.load()
        except Exception as exc:
            raise PluginLoadError(
                f"Could not load plugin '{self.name}' from {self.value!r}: {exc}"
            ) from exc
        protocol = ImageSourceAdapter if self.kind == "provider" else CMSAdapter
        try:
            conforms = isinstance(adapter_class, type) and issubclass(adapter_class, protocol)
        except TypeError:
            conforms = False
        if not conforms:
            raise PluginContractError(
                f"Plugin '{self.name}' from {self.value!r} does not implement "
                f"the {protocol.__name__} protocol"
            )
        return adapter_class

    def to_dict(self) -> Dict[str, str | None]:
        return {
            "name": self.name,
            "kind": self.kind,
            "entry_point": self.value,
            "distribution": self.distribution,
        }


def iter_plugins(kind: AdapterKind | None = None) -> list[AdapterPlugin]:
    """Return installed adapter plugins, sorted and checked for duplicates."""
    if kind is not None and kind not in ENTRY_POINT_GROUPS:
        raise ValueError(f"Unknown plugin kind: {kind}")

    kinds = (kind,) if kind else tuple(ENTRY_POINT_GROUPS)
    plugins: list[AdapterPlugin] = []
    seen: set[tuple[AdapterKind, str]] = set()

    for current_kind in kinds:
        group = ENTRY_POINT_GROUPS[current_kind]
        for entry_point in _entry_points_for(group):
            key = (current_kind, entry_point.name)
            if key in seen:
                raise DuplicatePluginError(
                    f"Multiple plugins registered as '{entry_point.name}' in {group}"
                )
            seen.add(key)
            distribution = None
            entry_point_distribution = getattr(entry_point, "dist", None)
            if entry_point_distribution is not None:
                distribution = entry_point_distribution.name
            plugins.append(AdapterPlugin(
                name=entry_point.name,
                kind=current_kind,
                value=entry_point.value,
                distribution=distribution,
                _entry_point=entry_point,
            ))

    return sorted(plugins, key=lambda plugin: (plugin.kind, plugin.name))


def load_plugin(kind: AdapterKind, name: str) -> Type[object]:
    """Load one installed plugin by kind and entry-point name."""
    for plugin in iter_plugins(kind):
        if plugin.name == name:
            return plugin.load()
    group = ENTRY_POINT_GROUPS.get(kind)
    if group is None:
        raise ValueError(f"Unknown plugin kind: {kind}")
    raise PluginNotFoundError(
        f"No {kind} plugin named '{name}' is installed (entry-point group: {group})"
    )


__all__ = [
    "AdapterKind",
    "AdapterPlugin",
    "DuplicatePluginError",
    "ENTRY_POINT_GROUPS",
    "PluginContractError",
    "PluginError",
    "PluginLoadError",
    "PluginNotFoundError",
    "iter_plugins",
    "load_plugin",
]
