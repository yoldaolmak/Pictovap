"""Openverse image source adapter — no credentials required.

Openverse (openverse.org, a WordPress/Wikimedia-affiliated project) indexes
openly licensed and public domain media aggregated from many sources. Its
search API requires no API key for basic use, which makes it a good
zero-friction second source alongside Unsplash.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List

_API_URL = "https://api.openverse.org/v1/images/"
_USER_AGENT = "Pictovap/0.2 (+https://github.com/yoldaolmak/Pictovap)"


def search_candidates(query: str, count: int) -> List[Dict[str, Any]]:
    """ImageSourceAdapter-conformant candidate search (no download).

    Only requests results licensed for commercial use and modification --
    a conservative default for a tool that places images into published
    articles. Returns an empty list (never raises) on any network or API
    error, so this adapter degrades gracefully even though it needs no
    credentials to begin with.
    """
    params = urllib.parse.urlencode({
        "q": query,
        "page_size": min(max(int(count), 1), 20),
        "license_type": "commercial,modification",
    })
    url = f"{_API_URL}?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, OSError, ValueError):
        return []

    results = data.get("results") or []
    candidates: List[Dict[str, Any]] = []
    for r in results[:count]:
        tags = [
            t.get("name", "") for t in (r.get("tags") or [])
            if isinstance(t, dict) and t.get("name")
        ]
        media_id = r.get("id", "")
        candidates.append({
            "id": f"openverse-{media_id}",
            "filename": f"openverse_{media_id}.jpg",
            "provider": "openverse",
            "source_type": "api",
            "local_path": None,
            "source_url": r.get("url"),
            "license": r.get("license", "unknown"),
            "attribution": r.get("creator") or None,
            "keywords": tags,
            "width": r.get("width") or 0,
            "height": r.get("height") or 0,
        })
    return candidates


class OpenverseSource:
    """Class wrapper matching the pattern used by LocalFolderSource,
    UnsplashSource, and DepositPhotosSource, so this adapter can be
    checked against ImageSourceAdapter the same way."""

    def search_candidates(self, query: str, count: int) -> List[Dict[str, Any]]:
        return search_candidates(query, count)


__all__ = ["search_candidates", "OpenverseSource"]
