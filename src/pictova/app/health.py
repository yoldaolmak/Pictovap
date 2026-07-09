"""Structured health checks for the application surface."""

from __future__ import annotations

import importlib
import os
import sqlite3
import sys
from typing import Dict, List

from pictova.config import get_vil_dir, get_visual_memory_db_path, load_project_env


REQUIRED_MODULES = ["PIL", "requests", "numpy", "cv2"]


def _db_stats(db_path: str) -> Dict:
    try:
        con = sqlite3.connect(db_path)
        row = con.execute("""
            SELECT
              COUNT(*) AS total,
              SUM(CASE WHEN source_path != '' THEN 1 ELSE 0 END) AS local_count,
              SUM(CASE WHEN source_path  = '' THEN 1 ELSE 0 END) AS icloud_count,
              SUM(CASE WHEN vision_scan_status = 'done'    THEN 1 ELSE 0 END) AS scanned,
              SUM(CASE WHEN vision_scan_status = 'pending' THEN 1 ELSE 0 END) AS pending,
              SUM(CASE WHEN vision_scan_status = 'error'   THEN 1 ELSE 0 END) AS errors
            FROM asset_index WHERE is_personal = 0
        """).fetchone()
        con.close()
        return {
            "total": row[0], "local": row[1], "icloud": row[2],
            "vision_scanned": row[3], "vision_pending": row[4], "vision_errors": row[5],
        }
    except Exception as exc:
        return {"error": str(exc)}


def _vision_chain_status() -> Dict:
    try:
        from pictova.engine.vision_chain import has_any_vision_source, _find_bin, _codex_check_login
        return {
            "any_source": has_any_vision_source(),
            "gemini_key": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
            "codex_logged_in": _codex_check_login(),
            "codex_bin": _find_bin("codex"),
            "claude_bin": _find_bin("claude"),
        }
    except Exception as exc:
        return {"error": str(exc)}


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

    db_path = str(get_visual_memory_db_path())
    return {
        "status": "ok" if not failed else "fail",
        "python": sys.version.split()[0],
        "vil_dir": str(get_vil_dir()),
        "visual_memory_db": db_path,
        "photo_index": _db_stats(db_path),
        "vision_chain": _vision_chain_status(),
        "anthropic_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "gemini_key": bool(os.environ.get("GEMINI_API_KEY")),
        "modules": modules,
    }
