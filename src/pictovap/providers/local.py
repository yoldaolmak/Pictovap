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
_GPS_INFO_TAG = 34853


def _json_safe_exif_value(value: Any) -> Any:
    """Return an EXIF value that can be serialized into a plan artifact."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _normalize_exif(exif: Any, tag_names: Dict[int, str]) -> Dict[str, Any]:
    """Normalize EXIF fields for JSON output while excluding precise GPS data."""
    normalized: Dict[str, Any] = {}
    for tag_id, value in exif.items():
        tag_name = tag_names.get(tag_id, str(tag_id))
        if tag_id == _GPS_INFO_TAG or tag_name == "GPSInfo":
            continue
        normalized[str(tag_name)] = _json_safe_exif_value(value)
    return normalized


def _read_image_metadata(path: Path) -> dict[str, Any]:
    """Return dimensions and JSON-safe, privacy-filtered EXIF fields."""
    try:
        from PIL import Image, ExifTags
        with Image.open(path) as img:
            meta: dict[str, Any] = {"width": img.width, "height": img.height}
            exif = img.getexif()
            if exif:
                exif_dict = _normalize_exif(exif, ExifTags.TAGS)
                if exif_dict:
                    meta["exif"] = exif_dict
            return meta
    except Exception:
        return {"width": 0, "height": 0}


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
            meta = _read_image_metadata(path)
            candidate = {
                "id": f"local-{path.stem}",
                "filename": path.name,
                "provider": "local",
                "source_type": "local",
                "local_path": str(path),
                "source_url": None,
                "license": "owned",
                "attribution": None,
                "keywords": [t for t in path.stem.replace("_", "-").split("-") if t],
                "width": meta.get("width", 0),
                "height": meta.get("height", 0),
            }
            if "exif" in meta:
                candidate["exif"] = meta["exif"]
            candidates.append(candidate)
            if len(candidates) >= count:
                break
        return candidates


__all__ = ["LocalFolderSource"]
