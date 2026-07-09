"""Local folder image source adapter.

Reads candidate images from a directory on disk. This is the simplest
possible ImageSourceAdapter implementation and requires no credentials,
making it a good reference for anyone writing a new source adapter.

Configure the directory via the `PICTOVAP_LOCAL_IMAGE_DIR` environment
variable, or pass `directory` explicitly.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _read_dimensions(path: Path) -> tuple[int, int]:
    """Return (width, height), or (0, 0) if the file can't be read as an image."""
    try:
        from PIL import Image
        with Image.open(path) as img:
            return img.size
    except Exception:
        return (0, 0)


class LocalFolderSource:
    """Image source adapter that lists files from a local directory."""

    def __init__(self, directory: str | None = None):
        self.directory = directory or os.environ.get("PICTOVAP_LOCAL_IMAGE_DIR", "")

    def search_candidates(self, query: str, count: int) -> List[Dict[str, Any]]:
        """Return up to `count` images found under `self.directory`.

        `query` is currently used only as a filename filter (substring
        match); it does not do content-based search. Returns an empty
        list if no directory is configured or it doesn't exist, so this
        adapter degrades gracefully rather than raising.
        """
        if not self.directory:
            return []
        root = Path(self.directory)
        if not root.is_dir():
            return []

        query_terms = [t for t in query.lower().split() if t]
        candidates: List[Dict[str, Any]] = []
        for path in sorted(root.rglob("*")):
            if path.suffix.lower() not in _IMAGE_EXTENSIONS:
                continue
            name_lower = path.stem.lower()
            if query_terms and not any(term in name_lower for term in query_terms):
                continue
            width, height = _read_dimensions(path)
            candidates.append(
                {
                    "id": f"local-{path.stem}",
                    "filename": path.name,
                    "provider": "local",
                    "source_type": "local",
                    "local_path": str(path),
                    "source_url": None,
                    "license": "owned",
                    "attribution": None,
                    "keywords": [t for t in path.stem.replace("_", "-").split("-") if t],
                    "width": width,
                    "height": height,
                }
            )
            if len(candidates) >= count:
                break
        return candidates


__all__ = ["LocalFolderSource"]
