"""Public helpers for testing third-party Pictovap adapters."""

from pictovap.testing.contracts import (
    ContractViolation,
    assert_cms_adapter_contract,
    assert_image_source_contract,
    assert_report_renderer_contract,
    sample_placement,
    validate_candidates,
    validate_placement_result,
)

__all__ = [
    "ContractViolation",
    "assert_cms_adapter_contract",
    "assert_image_source_contract",
    "assert_report_renderer_contract",
    "sample_placement",
    "validate_candidates",
    "validate_placement_result",
]
