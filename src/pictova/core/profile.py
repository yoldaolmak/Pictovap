"""
Publisher Profile definitions for Pictovap.

Defines the brand, styling, and CMS configuration for a specific deployment.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PublisherProfile:
    """
    Configuration model for a publisher profile.
    Decouples the core engine from specific site hardcoding.
    """
    profile_id: str
    brand_name: str
    cms_type: str = "wordpress"
    language: str = "en"
    image_sources: List[str] = field(default_factory=lambda: ["local", "unsplash"])
    output_rules: Dict[str, str] = field(default_factory=dict)
    filename_rules: Dict[str, str] = field(default_factory=dict)
    alt_text_rules: Dict[str, str] = field(default_factory=dict)
    caption_rules: Dict[str, str] = field(default_factory=dict)
    editorial_preferences: Dict[str, str] = field(default_factory=dict)
    forbidden_patterns: List[str] = field(default_factory=list)
    
    @classmethod
    def get_default_profile(cls) -> "PublisherProfile":
        """Returns a generic fallback profile."""
        return cls(
            profile_id="demo",
            brand_name="Demo Publisher",
            cms_type="wordpress",
            language="en"
        )
