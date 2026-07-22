"""Pixabay image-source adapter for Pictovap."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List

_API_URL = "https://pixabay.com/api/"
_USER_AGENT = "Pictovap-Pixabay-Example/0.1"


class PixabaySource:
    """Return image candidates from Pixabay."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def search_candidates(self, query: str, count: int) -> List[Dict[str, Any]]:
        """Search Pixabay and map results to the Pictovap candidate contract."""
        if not self.api_key or count <= 0:
            return []

        params = urllib.parse.urlencode({
            "key": self.api_key,
            "q": query,
            "image_type": "photo",
            "safesearch": "true",
            "per_page": min(int(count), 20),
        })
        request = urllib.request.Request(
            f"{_API_URL}?{params}",
            headers={"User-Agent": _USER_AGENT},
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.loads(response.read())
        except (urllib.error.URLError, OSError, ValueError, TypeError):
            return []

        hits = payload.get("hits") if isinstance(payload, dict) else None
        if not isinstance(hits, list):
            return []

        candidates: List[Dict[str, Any]] = []
        for hit in hits[:count]:
            if not isinstance(hit, dict):
                continue
            image_id = hit.get("id")
            source_url = hit.get("largeImageURL") or hit.get("webformatURL")
            width = hit.get("imageWidth")
            height = hit.get("imageHeight")
            if image_id is None or not source_url or not isinstance(width, int) or not isinstance(height, int):
                continue
            tags = [tag.strip() for tag in str(hit.get("tags") or "").split(",") if tag.strip()]
            candidates.append({
                "id": f"pixabay-{image_id}",
                "filename": f"pixabay_{image_id}.jpg",
                "provider": "pixabay",
                "source_type": "api",
                "local_path": None,
                "source_url": source_url,
                "license": "pixabay",
                "attribution": hit.get("user") or None,
                "keywords": tags,
                "width": width,
                "height": height,
            })
        return candidates


__all__ = ["PixabaySource"]
