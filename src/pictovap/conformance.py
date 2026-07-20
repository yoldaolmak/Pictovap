"""Safe, machine-readable conformance reports for installed adapter plugins."""

from __future__ import annotations

import contextlib
import io
from typing import Any, Literal, cast

from pictovap.app.runtime import construct_plugin
from pictovap.core.adapters import CMSAdapter, ImageSourceAdapter, ReportRenderer
from pictovap.testing import assert_image_source_contract, assert_report_renderer_contract

AdapterKind = Literal["provider", "cms", "renderer"]
_SENSITIVE_OPTION_MARKERS = ("key", "token", "password", "secret", "credential")


class AdapterCheckError(ValueError):
    """Raised when a conformance check cannot run safely."""


def _status(status: str, detail: str, **extra: Any) -> dict[str, Any]:
    return {"status": status, "detail": detail, **extra}


def _credential_values(options: dict[str, Any]) -> list[str]:
    return [
        str(value) for key, value in options.items()
        if any(marker in key.lower() for marker in _SENSITIVE_OPTION_MARKERS) and value
    ]


def check_adapter(
    *,
    kind: AdapterKind,
    name: str,
    options: dict[str, Any] | None = None,
    exercise: bool = False,
    query: str = "pictovap adapter check",
    count: int = 3,
) -> dict[str, Any]:
    """Return a safe conformance report for one installed plugin.

    The default check never calls ``search_candidates`` or ``CMSAdapter.place``.
    ``exercise=True`` is available only for provider adapters and explicitly
    runs one bounded search so returned provenance fields can be validated.
    """
    if kind not in {"provider", "cms", "renderer"}:
        raise AdapterCheckError(f"Unknown adapter kind: {kind}")
    if not name:
        raise AdapterCheckError("Adapter name is required")
    if type(count) is not int or count < 0:
        raise AdapterCheckError("Count must be a non-negative integer")
    if exercise and kind != "provider":
        raise AdapterCheckError("--exercise is currently supported only for provider adapters")

    resolved_options = dict(options or {})
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
        adapter = construct_plugin(kind, name, resolved_options)
    constructor_output = captured.getvalue()
    leaked = any(value in constructor_output for value in _credential_values(resolved_options))

    checks: dict[str, dict[str, Any]] = {
        "credential_leakage": _status(
            "failed" if leaked else "passed",
            "Constructor diagnostics were captured and credential option values were not emitted."
            if not leaked else "A credential option value was emitted during construction.",
        ),
        "dry_run": _status(
            "passed",
            "The adapter was loaded and constructed; no CMS placement or provider search ran.",
        ),
    }

    if kind == "provider":
        conforms = isinstance(adapter, ImageSourceAdapter)
        checks["source_adapter_contract"] = _status(
            "passed" if conforms else "failed",
            "Implements ImageSourceAdapter.search_candidates()." if conforms else
            "Does not implement ImageSourceAdapter.search_candidates().",
        )
        if exercise and conforms:
            candidates = assert_image_source_contract(
                cast(ImageSourceAdapter, adapter), query=query, count=count
            )
            checks["provenance_fields"] = _status(
                "passed",
                "Candidate provenance fields are JSON-safe and satisfy the public contract.",
                candidates_checked=len(candidates),
            )
            checks["dry_run"] = _status(
                "passed",
                "A bounded provider search ran; no CMS placement or write operation was invoked.",
            )
        else:
            checks["provenance_fields"] = _status(
                "not_run",
                "Run again with --exercise to validate returned candidate provenance fields.",
            )
    elif kind == "cms":
        conforms = isinstance(adapter, CMSAdapter)
        checks["cms_adapter_contract"] = _status(
            "passed" if conforms else "failed",
            "Implements CMSAdapter.place()." if conforms else "Does not implement CMSAdapter.place().",
        )
        checks["provenance_fields"] = _status("not_applicable", "CMS adapters consume an existing placement plan.")
    else:
        conforms = isinstance(adapter, ReportRenderer)
        checks["report_renderer_contract"] = _status(
            "passed" if conforms else "failed",
            "Implements ReportRenderer.render()." if conforms else "Does not implement ReportRenderer.render().",
        )
        if conforms:
            report = assert_report_renderer_contract(cast(ReportRenderer, adapter))
            checks["render_output"] = _status(
                "passed", "Rendered a non-empty report without writes.", length=len(report)
            )
        checks["provenance_fields"] = _status(
            "not_applicable", "Renderers consume a visual plan; they do not source images."
        )

    passed = all(check["status"] in {"passed", "not_applicable", "not_run"} for check in checks.values())
    return {
        "adapter": {"kind": kind, "name": name, "option_keys": sorted(resolved_options)},
        "status": "passed" if passed else "failed",
        "checks": checks,
    }


__all__ = ["AdapterCheckError", "check_adapter"]
