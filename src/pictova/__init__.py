"""
Pictovap — Open-source visual finishing engine for content publishers.

This package provides modules to select, process, generate metadata for, and
publish images across various CMS platforms.
"""

__version__ = "0.2.0"

# Core engine
from .engine.vision_chain import analyze_image_vision_chain
from .engine.selector import resolve_source_images

# CMS publishers
from .services.wordpress import YOWordPressUploader
from .publishers.ghost import GhostPublisher
from .publishers.strapi import StrapiPublisher

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
    "analyze_image_vision_chain",
    "resolve_source_images",
    "YOWordPressUploader",
    "GhostPublisher",
    "StrapiPublisher",
    "VisionTemplate",
    "TRAVEL_BLOG",
    "TECHNICAL",
    "MINIMAL",
    "ECOMMERCE",
    "get_template",
    "register_template",
]
