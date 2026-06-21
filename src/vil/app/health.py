"""Structured health checks for the application surface."""

from __future__ import annotations

import importlib
import os
import sys
from typing import Dict, List

from src.vil.config import get_vil_dir, get_visual_memory_db_path, load_project_env


REQUIRED_MODULES = ["PIL", "requests", "numpy", "cv2"]


def run_health_check() -> Dict:
    load_project_env()
    modules: List[Dict[str, str]] = []
    failed = False
    for name in REQUIRED_MODULES:
        try:
            importlib.import_module(name)
            modules.append({"module": name, "status": "ok"})
        except Exception as exc:
            failed = True
            modules.append({"module": name, "status": "fail", "error": str(exc)})

    return {
        "status": "ok" if not failed else "fail",
        "python": sys.version.split()[0],
        "vil_dir": str(get_vil_dir()),
        "visual_memory_db": str(get_visual_memory_db_path()),
        "anthropic_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "modules": modules,
    }
