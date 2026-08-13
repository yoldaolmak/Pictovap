"""Read-only discovery registry for built-in and installed adapters."""

from __future__ import annotations

import json
from typing import Any, Mapping

from pictovap.plugins import AdapterKind, PluginError, iter_plugins


_BUILT_INS: tuple[dict[str, Any], ...] = (
    {
        "name": "local",
        "kind": "provider",
        "source": "builtin",
        "description": "Local folder image source",
        "credentials": False,
    },
    {
        "name": "unsplash",
        "kind": "provider",
        "source": "builtin",
        "description": "Unsplash image source",
        "credentials": True,
    },
    {
        "name": "depositphotos",
        "kind": "provider",
        "source": "builtin",
        "description": "DepositPhotos image source",
        "credentials": True,
    },
    {
        "name": "openverse",
        "kind": "provider",
        "source": "builtin",
        "description": "Openverse image source",
        "credentials": False,
    },
    {
        "name": "pexels",
        "kind": "provider",
        "source": "builtin",
        "description": "Pexels image source",
        "credentials": True,
    },
    {
        "name": "wordpress",
        "kind": "cms",
        "source": "builtin",
        "description": "WordPress Gutenberg placement adapter",
        "credentials": True,
    },
    {
        "name": "ghost",
        "kind": "cms",
        "source": "builtin",
        "description": "Ghost CMS placement adapter",
        "credentials": True,
    },
    {
        "name": "strapi",
        "kind": "cms",
        "source": "builtin",
        "description": "Strapi CMS placement adapter",
        "credentials": True,
    },
    {
        "name": "markdown",
        "kind": "renderer",
        "source": "builtin",
        "description": "Markdown editor report renderer",
        "credentials": False,
    },
    {
        "name": "html",
        "kind": "renderer",
        "source": "builtin",
        "description": "HTML editor report renderer",
        "credentials": False,
    },
)


def registry_entries(kind: AdapterKind | None = None) -> list[dict[str, Any]]:
    """Return safe registry metadata without constructing or importing adapters."""
    if kind is not None and kind not in {"provider", "cms", "renderer"}:
        raise ValueError(f"Unknown registry kind: {kind}")

    entries = [dict(entry) for entry in _BUILT_INS if kind is None or entry["kind"] == kind]
    try:
        plugins = iter_plugins(kind)
    except PluginError:
        raise
    for plugin in plugins:
        entry = plugin.to_dict()
        entry.update({
            "source": "plugin",
            "description": f"Installed {plugin.kind} adapter plugin",
            "credentials": None,
        })
        entries.append(entry)
    return sorted(entries, key=lambda entry: (str(entry["kind"]), str(entry["name"]), str(entry["source"])))


def registry_payload(kind: AdapterKind | None = None) -> dict[str, Any]:
    """Return a machine-readable registry response."""
    entries = registry_entries(kind)
    return {
        "schema_version": "1",
        "status": "ready",
        "read_only": True,
        "entries": entries,
        "summary": {
            "total": len(entries),
            "builtin": sum(entry["source"] == "builtin" for entry in entries),
            "plugins": sum(entry["source"] == "plugin" for entry in entries),
        },
    }


def render_registry_markdown(payload: Mapping[str, Any]) -> str:
    """Render registry metadata for a contributor or release note."""
    summary = payload.get("summary", {})
    lines = [
        "# Pictovap Registry",
        "",
        f"**Adapters:** {summary.get('total', 0)} ({summary.get('builtin', 0)} built-in, "
        f"{summary.get('plugins', 0)} installed plugins)",
        "",
        "| Kind | Name | Source | Credentials | Description |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in payload.get("entries", []):
        credentials = (
            "yes" if entry.get("credentials") is True
            else "no" if entry.get("credentials") is False else "unknown"
        )
        lines.append(
            f"| `{entry.get('kind', '')}` | `{entry.get('name', '')}` | `{entry.get('source', '')}` | "
            f"{credentials} | {entry.get('description', '')} |"
        )
    lines.extend(["", "This registry is read-only; it never installs packages or calls external services.", ""])
    return "\n".join(lines)


def registry_to_json(payload: Mapping[str, Any]) -> str:
    """Serialize registry metadata with stable formatting."""
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


__all__ = ["registry_entries", "registry_payload", "registry_to_json", "render_registry_markdown"]
