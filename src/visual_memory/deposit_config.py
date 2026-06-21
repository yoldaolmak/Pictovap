"""
Deposit configuration module

Provides configuration management for licensed asset downloads.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional
import json


def load_deposit_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load deposit service configuration
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        Configuration dictionary
    """
    default_config = {
        'enabled': False,
        'api_key': None,
        'username': None,
        'password': None,
        'session_id': None,
        'download_dir': None
    }
    
    if config_path and config_path.exists():
        try:
            with open(config_path, 'r') as f:
                loaded = json.load(f)
                default_config.update(loaded)
        except Exception:
            pass
    
    return default_config
