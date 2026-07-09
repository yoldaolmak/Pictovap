"""Deposit configuration helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


def load_deposit_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    default_config = {
        "enabled": False,
        "api_key": None,
        "username": None,
        "password": None,
        "session_id": None,
        "download_dir": None,
    }
    if config_path and config_path.exists():
        try:
            default_config.update(json.loads(config_path.read_text()))
        except Exception:
            pass
    return default_config
