from __future__ import annotations

import os
from pathlib import Path


_ENV_LOADED = False


def get_workspace_root() -> Path:
    """Root directory for Pictovap's runtime files (`.env` lookup, `data/`).

    Defaults to the current working directory — the user's own project —
    never the package installation directory. Resolving paths relative to
    this module would point inside site-packages for a real
    `pip install pictovap`, which is unwritable and wrong.

    Override with the ``PICTOVA_WORKSPACE_DIR`` environment variable. This
    is read from the process environment directly (not `.env`), because the
    `.env` location itself depends on this value.
    """
    configured = os.environ.get("PICTOVA_WORKSPACE_DIR", "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path.cwd()


def load_project_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    env_path = get_workspace_root() / ".env"
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
