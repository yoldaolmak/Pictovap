"""
Pictovap — Open-source visual finishing engine for content publishers.

This package provides modules to select, process, generate metadata for, and
publish images across various CMS platforms.
"""

__version__ = "0.3.0"

# Public library API — the framework entry point.
from .demo import create_visual_plan

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

__all__ = [
    "create_visual_plan",
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
