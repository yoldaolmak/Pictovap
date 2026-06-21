"""Product core engine surface."""

from src.vil.engine.attach import (
    build_attach_plan,
    build_process_result,
    build_failed_attach_result,
    derive_location_query,
    execute_native_attach,
    execute_legacy_attach,
    normalize_attach_result,
    prepare_attach_request,
    summarize_post_context,
    validate_attach_request,
)

__all__ = [
    "build_attach_plan",
    "build_process_result",
    "build_failed_attach_result",
    "derive_location_query",
    "execute_native_attach",
    "execute_legacy_attach",
    "normalize_attach_result",
    "prepare_attach_request",
    "summarize_post_context",
    "validate_attach_request",
]
