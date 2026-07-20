"""Reusable contract assertions for third-party adapter test suites."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, cast

from pictovap.core.adapters import CMSAdapter, ImageSourceAdapter, ReportRenderer
from pictovap.core.primitives import CMSPlacement, PlacementInstruction

REQUIRED_CANDIDATE_FIELDS = frozenset({
    "id",
    "filename",
    "provider",
    "source_type",
    "local_path",
    "source_url",
    "license",
    "attribution",
    "keywords",
    "width",
    "height",
})
REQUIRED_PLACEMENT_RESULT_FIELDS = frozenset({"placed", "failed", "warnings"})


class ContractViolation(AssertionError):
    """Raised when an adapter returns data outside the public contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractViolation(message)


def validate_candidates(candidates: Any, *, maximum: int | None = None) -> None:
    """Validate the output of ``ImageSourceAdapter.search_candidates``."""
    _require(isinstance(candidates, list), "search_candidates() must return a list")
    if maximum is not None:
        _require(len(candidates) <= maximum, f"adapter returned more than {maximum} candidates")

    for index, candidate in enumerate(candidates):
        prefix = f"candidate[{index}]"
        _require(isinstance(candidate, Mapping), f"{prefix} must be a mapping")
        missing = REQUIRED_CANDIDATE_FIELDS - candidate.keys()
        _require(not missing, f"{prefix} is missing fields: {', '.join(sorted(missing))}")
        _require(candidate["source_type"] in {"local", "api", "url"},
                 f"{prefix}.source_type must be local, api, or url")
        _require(isinstance(candidate["keywords"], list), f"{prefix}.keywords must be a list")
        _require(all(isinstance(keyword, str) for keyword in candidate["keywords"]),
                 f"{prefix}.keywords must contain only strings")
        for field in ("id", "filename", "provider", "license"):
            _require(isinstance(candidate[field], str), f"{prefix}.{field} must be a string")
        for field in ("local_path", "source_url", "attribution"):
            _require(candidate[field] is None or isinstance(candidate[field], str),
                     f"{prefix}.{field} must be a string or null")
        _require(candidate["local_path"] is not None or candidate["source_url"] is not None,
                 f"{prefix} must provide local_path or source_url")
        _require(type(candidate["width"]) is int, f"{prefix}.width must be an integer")
        _require(type(candidate["height"]) is int, f"{prefix}.height must be an integer")
        _require(candidate["width"] > 0, f"{prefix}.width must be positive")
        _require(candidate["height"] > 0, f"{prefix}.height must be positive")
        try:
            json.dumps(candidate)
        except (TypeError, ValueError) as exc:
            raise ContractViolation(f"{prefix} must be JSON-serializable: {exc}") from exc


def validate_placement_result(result: Any) -> None:
    """Validate the output of ``CMSAdapter.place``."""
    _require(isinstance(result, Mapping), "place() must return a mapping")
    missing = REQUIRED_PLACEMENT_RESULT_FIELDS - result.keys()
    _require(not missing, f"placement result is missing fields: {', '.join(sorted(missing))}")
    for field in REQUIRED_PLACEMENT_RESULT_FIELDS:
        _require(isinstance(result[field], list), f"placement result '{field}' must be a list")
    try:
        json.dumps(result)
    except (TypeError, ValueError) as exc:
        raise ContractViolation(f"placement result must be JSON-serializable: {exc}") from exc


def assert_image_source_contract(
    adapter: object,
    *,
    query: str = "pictovap contract test",
    count: int = 3,
) -> list[dict[str, Any]]:
    """Run an image-source adapter once and validate its complete contract.

    Network calls should be mocked by the caller. Empty results are valid.
    """
    _require(type(count) is int and count >= 0, "count must be a non-negative integer")
    _require(isinstance(adapter, ImageSourceAdapter),
             "adapter must implement ImageSourceAdapter.search_candidates")
    provider = cast(ImageSourceAdapter, adapter)
    candidates = provider.search_candidates(query, count)
    validate_candidates(candidates, maximum=count)
    return candidates


def sample_placement() -> CMSPlacement:
    """Return a minimal placement fixture suitable for CMS adapter tests."""
    return CMSPlacement(
        article_id="contract-test",
        placements=[PlacementInstruction(
            slot_id="featured",
            output_path="/tmp/pictovap-contract-test.webp",
            image_role="featured",
            alt_text="Contract test image",
            caption="Pictovap contract test",
        )],
    )


def assert_cms_adapter_contract(
    adapter: object,
    *,
    placement: CMSPlacement | None = None,
) -> dict[str, Any]:
    """Run a CMS adapter once and validate its complete result contract.

    Network and filesystem calls should be mocked by the caller.
    """
    _require(isinstance(adapter, CMSAdapter), "adapter must implement CMSAdapter.place")
    cms_adapter = cast(CMSAdapter, adapter)
    result = cms_adapter.place(placement or sample_placement())
    validate_placement_result(result)
    return dict(result)


def assert_report_renderer_contract(
    renderer: object,
    *,
    plan: dict[str, Any] | None = None,
) -> str:
    """Run a renderer once and validate its public output contract."""
    _require(isinstance(renderer, ReportRenderer), "renderer must implement ReportRenderer.render")
    report = cast(ReportRenderer, renderer).render(plan or {"visual_brief": {}, "profile": {}})
    _require(isinstance(report, str), "render() must return a string")
    _require(bool(report.strip()), "render() must return a non-empty string")
    return report


__all__ = [
    "ContractViolation",
    "REQUIRED_CANDIDATE_FIELDS",
    "REQUIRED_PLACEMENT_RESULT_FIELDS",
    "assert_cms_adapter_contract",
    "assert_image_source_contract",
    "assert_report_renderer_contract",
    "sample_placement",
    "validate_candidates",
    "validate_placement_result",
]
