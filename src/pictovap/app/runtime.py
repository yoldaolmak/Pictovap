"""Application service that connects installed plugins to Pictovap workflows."""

from __future__ import annotations

import inspect
import json
import os
import platform
from pathlib import Path
from typing import Any, Iterable, cast

from pictovap import __version__
from pictovap.core.primitives import CMSPlacement
from pictovap.demo import create_visual_plan, create_wordpress_visual_plan
from pictovap.plugins import AdapterKind, iter_plugins, load_plugin
from pictovap.testing.contracts import validate_placement_result


class RuntimeConfigurationError(ValueError):
    """Raised when adapter configuration cannot be resolved safely."""


class AdapterConstructionError(RuntimeError):
    """Raised when an installed adapter cannot be constructed."""


def parse_adapter_options(items: Iterable[str] | None) -> dict[str, Any]:
    """Parse repeatable ``key=value`` options without exposing secret values.

    JSON scalars are decoded, so ``count=3`` and ``enabled=true`` retain their
    types. ``key=@ENV_NAME`` reads a value from the environment; ``@@value``
    escapes a literal leading ``@``.
    """
    options: dict[str, Any] = {}
    for item in items or ():
        key, separator, raw_value = item.partition("=")
        if not separator or not key.isidentifier():
            raise RuntimeConfigurationError(
                f"Invalid adapter option '{item}'. Use key=value."
            )
        if key in options:
            raise RuntimeConfigurationError(f"Adapter option '{key}' was provided more than once")
        if raw_value.startswith("@@"):
            value: Any = raw_value[1:]
        elif raw_value.startswith("@"):
            variable = raw_value[1:]
            if not variable or variable not in os.environ:
                raise RuntimeConfigurationError(
                    f"Environment variable '{variable}' required by option '{key}' is not set"
                )
            value = os.environ[variable]
        else:
            try:
                value = json.loads(raw_value)
            except json.JSONDecodeError:
                value = raw_value
        options[key] = value
    return options


def construct_plugin(
    kind: AdapterKind,
    name: str,
    options: dict[str, Any] | None = None,
) -> object:
    """Load and construct one installed plugin with actionable safe errors."""
    adapter_class = load_plugin(kind, name)
    resolved = dict(options or {})
    signature = inspect.signature(adapter_class)
    try:
        signature.bind(**resolved)
    except TypeError as exc:
        accepted = ", ".join(signature.parameters) or "no options"
        raise AdapterConstructionError(
            f"Cannot configure {kind} plugin '{name}'. Accepted options: {accepted}. "
            f"Received option keys: {', '.join(sorted(resolved)) or 'none'}."
        ) from exc
    try:
        return adapter_class(**resolved)
    except Exception as exc:
        raise AdapterConstructionError(
            f"{kind.capitalize()} plugin '{name}' failed during construction. "
            f"Received option keys: {', '.join(sorted(resolved)) or 'none'}."
        ) from exc


def _read_placement(plan_path: str | Path, cms_name: str) -> CMSPlacement:
    path = Path(plan_path)
    if not path.exists():
        raise FileNotFoundError(f"Plan not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Plan is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Plan root must be an object")
    placement_data = payload.get("cms_placement", payload)
    placement = CMSPlacement.from_dict(placement_data)
    placement.adapter_target = cms_name
    placement.target_platform = cms_name
    return placement


class PipelineRunner:
    """Run plan, health-check, and publish workflows through installed plugins."""

    def doctor(
        self,
        *,
        provider: str | None = None,
        cms: str | None = None,
        provider_options: dict[str, Any] | None = None,
        cms_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Load every plugin and construct explicitly selected adapters.

        CMS ``place`` is deliberately not called: doctor has no write effects.
        Provider search is exercised by ``plan``, where a meaningful query and
        complete contract validation are available.
        """
        if provider_options and not provider:
            raise RuntimeConfigurationError("Provider options require --provider")
        if cms_options and not cms:
            raise RuntimeConfigurationError("CMS options require --cms")

        plugins = []
        discovered = iter_plugins()
        for plugin in discovered:
            record: dict[str, Any] = plugin.to_dict()
            try:
                plugin.load()
                record["load"] = "ok"
            except Exception as exc:
                record["load"] = "error"
                record["error"] = str(exc)
            plugins.append(record)

        selected: dict[str, dict[str, Any]] = {}
        for kind, name, options in (
            ("provider", provider, provider_options),
            ("cms", cms, cms_options),
        ):
            if name:
                construct_plugin(cast(AdapterKind, kind), name, options)
                selected[kind] = {
                    "name": name,
                    "construction": "ok",
                    "option_keys": sorted((options or {}).keys()),
                }

        healthy = all(plugin["load"] == "ok" for plugin in plugins)
        return {
            "status": "ready" if healthy else "unhealthy",
            "pictovap": __version__,
            "python": platform.python_version(),
            "plugins": plugins,
            "selected": selected,
            "checks": {
                "discovery": "ok",
                "contracts": "ok" if healthy else "failed",
                "write_effects": "not_run",
            },
        }

    def plan(
        self,
        *,
        article: str,
        profile: str | None = None,
        output: str | None = None,
        report: str | None = None,
        provider: str | None = None,
        provider_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a plan, using an installed provider when explicitly named."""
        if provider_options and not provider:
            raise RuntimeConfigurationError("Provider options require --provider")
        adapter = construct_plugin("provider", provider, provider_options) if provider else None
        return create_visual_plan(
            article=article,
            profile=profile,
            output=output,
            report=report,
            provider_adapter=adapter,
            provider_name=provider,
        )

    def publish(
        self,
        *,
        plan: str,
        cms: str,
        cms_options: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Validate a plan and pass its typed placement to an installed CMS plugin."""
        placement = _read_placement(plan, cms)
        adapter = construct_plugin("cms", cms, cms_options)
        envelope: dict[str, Any] = {
            "status": "ready" if dry_run else "completed",
            "mode": "dry-run" if dry_run else "publish",
            "cms": {"name": cms, "option_keys": sorted((cms_options or {}).keys())},
            "placement": placement.to_dict(),
            "summary": {"planned": len(placement.placements)},
        }
        if dry_run:
            return envelope

        result = adapter.place(placement)  # type: ignore[attr-defined]
        validate_placement_result(result)
        envelope["result"] = dict(result)
        envelope["status"] = "partial" if result["failed"] else "completed"
        return envelope

    def plan_wordpress_post(
        self,
        *,
        post_id: int,
        site: str = "demo",
        profile: str | None = None,
        output: str | None = None,
        report: str | None = None,
        provider: str | None = None,
        provider_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a plan from a WordPress Gutenberg post without writing to it."""
        if provider_options and not provider:
            raise RuntimeConfigurationError("Provider options require --provider")
        adapter = construct_plugin("provider", provider, provider_options) if provider else None
        return create_wordpress_visual_plan(
            post_id,
            site=site,
            profile=profile,
            output=output,
            report=report,
            provider_adapter=adapter,
            provider_name=provider,
        )


__all__ = [
    "AdapterConstructionError",
    "PipelineRunner",
    "RuntimeConfigurationError",
    "construct_plugin",
    "parse_adapter_options",
]
