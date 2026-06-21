"""Job wrappers around the canonical engine."""

from __future__ import annotations

from typing import Any, Dict

from src.vil.engine.attach import (
    execute_legacy_attach,
    prepare_attach_request,
    validate_attach_request,
)


def run_attach_job(**kwargs: Any) -> Dict[str, Any]:
    site = kwargs.get("site", "yoldaolmak")
    request, post_context, constraints = prepare_attach_request(**kwargs)
    failed = validate_attach_request(
        site=site,
        request=request,
        post_context=post_context,
        constraints=constraints,
    )
    if failed:
        return failed
    return execute_legacy_attach(
        site=site,
        request=request,
        post_context=post_context,
        constraints=constraints,
    )
