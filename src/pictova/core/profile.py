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
    language_mode: str = "fallback"  # fallback | override
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
            language="en",
            language_mode="fallback"
        )

    @classmethod
    def from_yaml(cls, path: str) -> "PublisherProfile":
        """Loads a publisher profile from a YAML file (simple parser to avoid external dependencies)."""
        from pathlib import Path
        content = Path(path).read_text(encoding="utf-8")
        data = {}
        current_key = None
        for line in content.splitlines():
            line = line.split('#')[0].rstrip()
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip())
            line_str = line.strip()
            
            if line_str.startswith("-"):
                val = line_str[1:].strip()
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                if current_key:
                    if not isinstance(data.get(current_key), list):
                        data[current_key] = []
                    data[current_key].append(val)
            elif ":" in line_str:
                parts = line_str.split(":", 1)
                k = parts[0].strip()
                v = parts[1].strip()
                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                    v = v[1:-1]
                elif v.isdigit():
                    v = int(v)
                elif v.lower() == "true":
                    v = True
                elif v.lower() == "false":
                    v = False
                elif v == "":
                    v = None
                    
                if indent == 0:
                    current_key = k
                    data[k] = v
                else:
                    if current_key:
                        if not isinstance(data.get(current_key), dict):
                            data[current_key] = {}
                        data[current_key][k] = v
                        
        return cls(
            profile_id=data.get("profile_id", "unknown"),
            brand_name=data.get("brand_name", "Unknown Publisher"),
            cms_type=data.get("cms_type", "wordpress"),
            language=data.get("language", "en"),
            language_mode=data.get("language_mode", "fallback"),
            image_sources=data.get("image_sources") or ["local", "unsplash"],
            output_rules=data.get("output_rules") or {},
            filename_rules=data.get("filename_rules") or {},
            alt_text_rules=data.get("alt_text_rules") or {},
            caption_rules=data.get("caption_rules") or {},
            editorial_preferences=data.get("editorial_preferences") or {},
            forbidden_patterns=data.get("forbidden_patterns") or []
        )
