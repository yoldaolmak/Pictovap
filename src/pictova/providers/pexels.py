"""Pexels image source adapter.

Requires a free Pexels API key (PEXELS_API_KEY). Sign up at
https://www.pexels.com/api/ -- approval is typically instant and the free
tier (200 requests/hour, 20,000/month) is enough for most publishers.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List

from pictova.utils.config import env_str, load_project_env

load_project_env()

_API_URL = "https://api.pexels.com/v1/search"


def _api_key() -> str:
    return env_str("PEXELS_API_KEY", "") or ""


def search_candidates(query: str, count: int) -> List[Dict[str, Any]]:
    """ImageSourceAdapter-conformant candidate search (no download).

    Returns an empty list (never raises) when PEXELS_API_KEY is not set,
    or on any network/API error, so this adapter degrades gracefully when
    unconfigured or unreachable.
    """
    api_key = _api_key()
    if not api_key:
        return []

    params = urllib.parse.urlencode({
        "query": query,
        "per_page": min(max(int(count), 1), 80),
    })
    url = f"{_API_URL}?{params}"

    try:
        req = urllib.request.Request(url, headers={"Authorization": api_key})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, OSError, ValueError):
        return []

    photos = data.get("photos") or []
    candidates: List[Dict[str, Any]] = []
    for p in photos[:count]:
        src = p.get("src") or {}
        photo_id = p.get("id", "")
        alt = (p.get("alt") or "").strip()
        candidates.append({
            "id": f"pexels-{photo_id}",
            "filename": f"pexels_{photo_id}.jpg",
            "provider": "pexels",
            "source_type": "api",
            "local_path": None,
            "source_url": src.get("original") or src.get("large2x") or src.get("large"),
            "license": "pexels",
            "attribution": p.get("photographer"),
            "keywords": [w for w in alt.split() if w],
            "width": p.get("width") or 0,
            "height": p.get("height") or 0,
        })
    return candidates


class PexelsSource:
    """Class wrapper matching the pattern used by the other image source
    adapters, so this one can be checked against ImageSourceAdapter the
    same way."""

    def search_candidates(self, query: str, count: int) -> List[Dict[str, Any]]:
        return search_candidates(query, count)


__all__ = ["search_candidates", "PexelsSource"]
