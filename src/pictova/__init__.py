"""
Pictova SDK — Visual intelligence layer for content publishers.

This package provides modules to select, process, generate metadata for, and
publish images across various CMS platforms.
"""

__version__ = "0.2.0"

# Expose core functionality to developers
from .engine.vision_chain import analyze_image_vision_chain
from .engine.selector import resolve_source_images
from .services.wordpress import YOWordPressUploader

__all__ = [
    "analyze_image_vision_chain",
    "resolve_source_images",
    "YOWordPressUploader",
]
