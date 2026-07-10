from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_VISUAL_MEMORY_DB = PROJECT_ROOT / "data" / "visual_memory.db"
_ENV_LOADED = False


def load_project_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" not in line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

    _ENV_LOADED = True


def env_str(name: str, default: str | None = None) -> str | None:
    load_project_env()
    value = os.environ.get(name)
    if value is None:
        return default
    stripped = value.strip()
    if not stripped:
        return default
    return stripped


def get_vil_dir() -> Path | None:
    """Local staging directory for the optional Unsplash `download()`
    convenience method (see `providers/unsplash.py`). Not required for the
    documented `search_candidates()` path used by the pipeline.

    No personal-machine default: returns None when unset, matching the
    graceful-degradation pattern of `env_str()` above rather than hardcoding
    a path specific to any one contributor's machine.
    """
    configured = env_str("YO_VIL_DIR")
    if configured:
        return Path(configured).expanduser()
    return None


def get_visual_memory_db_path() -> Path:
    configured = env_str("YO_VISUAL_MEMORY_DB")
    if configured:
        return Path(configured).expanduser()
    return DEFAULT_VISUAL_MEMORY_DB
