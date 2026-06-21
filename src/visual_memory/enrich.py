"""
Enrichment module for visual memory records

Provides utilities to enrich image metadata with additional information.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional


def enrich_record(record: Dict[str, Any], image_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Enrich an image record with additional metadata
    
    Args:
        record: Existing image record
        image_path: Optional path to image file for additional analysis
        
    Returns:
        Enriched record dictionary
    """
    enriched = record.copy()
    
    # Add derived fields
    if 'path' in record and not image_path:
        image_path = Path(record['path'])
    
    if image_path and image_path.exists():
        try:
            stat = image_path.stat()
            enriched['file_size'] = stat.st_size
            enriched['last_modified'] = stat.st_mtime
        except Exception:
            pass
    
    # Add quality score placeholder
    if 'width' in record and 'height' in record:
        megapixels = (record['width'] * record['height']) / 1_000_000
        enriched['megapixels'] = round(megapixels, 2)
    
    return enriched
