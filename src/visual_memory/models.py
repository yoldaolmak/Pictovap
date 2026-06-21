"""
Visual Memory Models - Data classes for stock image integration

This module defines the data structures used for stock photo service
integration, including connection status and search results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class StockConnectionStatus:
    """Status of connection to stock photo service"""
    connected: bool = False
    auth_mode: Optional[str] = None
    endpoint: Optional[str] = None
    search_enabled: bool = False
    message: Optional[str] = None


@dataclass
class StockSearchResult:
    """Result from stock photo search"""
    asset_id: str
    title: Optional[str] = None
    preview_url: Optional[str] = None
    landing_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    contributor: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
