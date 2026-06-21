"""
Sources module for visual memory

Provides data structures for discovered images from various sources.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class DiscoveredImage:
    """Represents an image discovered from a source"""
    path: Path
    filename: str
    source: str = 'local'
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_path(cls, path: Path, source: str = 'local') -> 'DiscoveredImage':
        """Create DiscoveredImage from a file path"""
        return cls(
            path=path,
            filename=path.name,
            source=source
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'path': str(self.path),
            'filename': self.filename,
            'source': self.source,
            'width': self.width,
            'height': self.height,
            'file_size': self.file_size,
            'tags': self.tags,
            'metadata': self.metadata
        }
