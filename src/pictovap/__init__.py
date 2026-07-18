"""
Pictovap — Open-source visual finishing engine for content publishers.

This package provides modules to select, process, generate metadata for, and
publish images across various CMS platforms.
"""

from typing import TYPE_CHECKING, Any

__version__ = "0.7.1"

if TYPE_CHECKING:
    from .demo import create_visual_plan as create_visual_plan
    from .demo import create_wordpress_visual_plan as create_wordpress_visual_plan

# Adapter contracts
from .core.adapters import ImageSourceAdapter, CMSAdapter, ReportRenderer

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
        from . import demo

        return getattr(demo, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "create_visual_plan",
    "create_wordpress_visual_plan",
    "ImageSourceAdapter",
    "CMSAdapter",
    "ReportRenderer",
    "VisionTemplate",
    "TRAVEL_BLOG",
    "TECHNICAL",
    "MINIMAL",
    "ECOMMERCE",
    "get_template",
    "register_template",
]
