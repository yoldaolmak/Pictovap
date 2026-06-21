"""
Analyzer module for visual memory

Provides image analysis utilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional


def analyze_image(image_path: Path) -> Dict[str, Any]:
    """
    Analyze an image and return metadata
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary containing image analysis results
    """
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'size_bytes': image_path.stat().st_size,
                'path': str(image_path),
                'filename': image_path.name
            }
    except Exception as e:
        return {
            'error': str(e),
            'path': str(image_path),
            'filename': image_path.name
        }
