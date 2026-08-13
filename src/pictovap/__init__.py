"""
Pictovap — Open-source visual finishing engine for content publishers.

This package provides modules to select, process, generate metadata for, and
publish images across various CMS platforms.
"""

from typing import TYPE_CHECKING, Any

__version__ = "0.13.0"

if TYPE_CHECKING:
    from .api import create_visual_plan as create_visual_plan
    from .api import create_wordpress_visual_plan as create_wordpress_visual_plan

# Adapter contracts
from .core.adapters import ImageSourceAdapter, CMSAdapter, ReportRenderer
from .core.selection import SelectionPolicy, SelectionResult, select_assignments
from .core.visual_similarity import compute_visual_fingerprint, visual_similarity
from .validation import validate_visual_plan
from .audit import audit_visual_plan, render_audit_markdown
from .benchmark import benchmark_to_json, render_benchmark_markdown, run_corpus_benchmark
from .registry import registry_entries, registry_payload, registry_to_json, render_registry_markdown
from .intent import (
    build_decision_ledger,
    build_visual_intent_graph,
    compile_intent_proof,
    intent_proof_to_json,
    render_intent_markdown,
)
from .renderers import HTMLReportRenderer, MarkdownReportRenderer

# Vision template system
from .vision_templates import (
    VisionTemplate,
    TRAVEL_BLOG,
    TECHNICAL,
    MINIMAL,
    ECOMMERCE,
    get_template,
    register_template,
)


def __getattr__(name: str) -> Any:
    """Load the demo-backed public API without importing it during package initialization."""
    if name in {"create_visual_plan", "create_wordpress_visual_plan"}:
        from . import api

        return getattr(api, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "create_visual_plan",
    "create_wordpress_visual_plan",
    "ImageSourceAdapter",
    "CMSAdapter",
    "ReportRenderer",
    "SelectionPolicy",
    "SelectionResult",
    "select_assignments",
    "compute_visual_fingerprint",
    "visual_similarity",
    "validate_visual_plan",
    "audit_visual_plan",
    "render_audit_markdown",
    "run_corpus_benchmark",
    "render_benchmark_markdown",
    "benchmark_to_json",
    "registry_entries",
    "registry_payload",
    "registry_to_json",
    "render_registry_markdown",
    "build_decision_ledger",
    "build_visual_intent_graph",
    "compile_intent_proof",
    "intent_proof_to_json",
    "render_intent_markdown",
    "HTMLReportRenderer",
    "MarkdownReportRenderer",
    "VisionTemplate",
    "TRAVEL_BLOG",
    "TECHNICAL",
    "MINIMAL",
    "ECOMMERCE",
    "get_template",
    "register_template",
]
