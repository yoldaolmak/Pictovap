"""Wikimedia image-source adapter for Pictovap."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List

_API_URL = "https://commons.wikimedia.org/w/api.php"
_USER_AGENT = "Pictovap-Wikimedia-Example/0.1 (https://github.com/yoldaolmak/Pictovap)"


def _metadata_value(metadata: Any, key: str) -> str | None:
    value = metadata.get(key) if isinstance(metadata, dict) else None
    raw = value.get("value") if isinstance(value, dict) else value
    if not raw:
        return None
    return re.sub(r"<[^>]+>", "", str(raw)).strip() or None


class WikimediaSource:
    """Return image candidates from Wikimedia."""

    def search_candidates(self, query: str, count: int) -> List[Dict[str, Any]]:
        """Search Wikimedia Commons and preserve per-file provenance metadata."""
        if count <= 0:
            return []

        params = urllib.parse.urlencode({
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": min(int(count), 20),
            "prop": "imageinfo",
            "iiprop": "url|size|extmetadata",
            "format": "json",
            "formatversion": 2,
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

        pages = ((payload.get("query") or {}).get("pages")) if isinstance(payload, dict) else None
        if not isinstance(pages, list):
            return []

        keywords = [word for word in re.split(r"\s+", query.strip()) if word]
        candidates: List[Dict[str, Any]] = []
        for page in pages[:count]:
            if not isinstance(page, dict):
                continue
            imageinfo = page.get("imageinfo")
            info = imageinfo[0] if isinstance(imageinfo, list) and imageinfo else None
            if not isinstance(info, dict):
                continue
            source_url = info.get("url")
            width = info.get("width")
            height = info.get("height")
            if not source_url or not isinstance(width, int) or not isinstance(height, int):
                continue
            metadata = info.get("extmetadata") or {}
            title = str(page.get("title") or "").removeprefix("File:")
            page_id = page.get("pageid") or title
            candidates.append({
                "id": f"wikimedia-{page_id}",
                "filename": title or f"wikimedia_{page_id}",
                "provider": "wikimedia",
                "source_type": "api",
                "local_path": None,
                "source_url": source_url,
                "license": _metadata_value(metadata, "LicenseShortName")
                or _metadata_value(metadata, "UsageTerms")
                or "unknown",
                "attribution": _metadata_value(metadata, "Artist"),
                "keywords": keywords,
                "width": width,
                "height": height,
            })
        return candidates


__all__ = ["WikimediaSource"]
