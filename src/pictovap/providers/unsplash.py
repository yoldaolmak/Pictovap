#!/usr/bin/env python3
"""Unsplash image source adapter."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from typing import Dict, List

import requests

from pictovap.utils.config import get_vil_dir, load_project_env

load_project_env()


class UnsplashSource:
    """Download travel photos from Unsplash by query."""

    def __init__(self):
        # Per the ImageSourceAdapter contract (core/adapters.py), construction
        # must never require credentials — a missing UNSPLASH_ACCESS_KEY is
        # only surfaced as an empty result once a search is attempted, so
        # this class stays usable in a credential-free pipeline.
        self.access_key = os.environ.get("UNSPLASH_ACCESS_KEY")
        self.api_url = os.environ.get("UNSPLASH_API_URL", "https://api.unsplash.com")
        # Optional local staging directory for download(); unset by default
        # (no personal-machine path), only created when actually configured.
        self.vil_dir = get_vil_dir()
        if self.vil_dir:
            self.vil_dir.mkdir(parents=True, exist_ok=True)

    def search(self, query: str, count: int = 5, page: int = 1) -> List[Dict]:
        if not self.access_key:
            return []
        url = f"{self.api_url}/search/photos"
        params = {
            "client_id": self.access_key,
            "query": query,
            "page": page,
            "per_page": count,
            "order_by": "relevant",
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json().get("results", [])
        except Exception:
            return []

    def download(
        self, query: str, count: int = 5, naming_template: str = "{location}-{number}"
    ) -> List[str]:
        if not self.vil_dir:
            raise RuntimeError(
                "download() requires a local staging directory. Set YO_VIL_DIR "
                "in .env to enable it — search_candidates() does not need this."
            )
        results = self.search(query, count=count)
        downloaded = []
        for i, result in enumerate(results[:count], 1):
            try:
                download_url = result["links"]["download"]
                photo_id = result["id"]
                user_name = result["user"]["username"]
                alt_text = result.get("alt_description", "Unsplash photo")
                location = query.split()[0].lower()
                filename = naming_template.format(location=location, number=i).replace(" ", "-")
                if not filename.endswith((".jpg", ".png", ".webp")):
                    filename += ".jpg"
                filepath = self.vil_dir / filename
                headers = {"Authorization": f"Client-ID {self.access_key}"}
                resp = requests.get(download_url, headers=headers, timeout=30)
                resp.raise_for_status()
                filepath.write_bytes(resp.content)
                metadata = {
                    "source": "unsplash",
                    "photo_id": photo_id,
                    "user": user_name,
                    "query": query,
                    "alt": alt_text,
                    "download_url": download_url,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                filepath.with_suffix(".json").write_text(
                    json.dumps(metadata, indent=2, ensure_ascii=False)
                )
                downloaded.append(str(filepath))
            except Exception:
                continue
        return downloaded

    def search_candidates(self, query: str, count: int) -> List[Dict]:
        """ImageSourceAdapter-conformant candidate search (no download).

        Returns the standard candidate dict shape without fetching the
        actual image bytes; the pipeline downloads only selected images.
        """
        results = self.search(query, count=count)
        candidates: List[Dict] = []
        for r in results[:count]:
            candidates.append(
                {
                    "id": f"unsplash-{r.get('id')}",
                    "filename": f"{r.get('id')}.jpg",
                    "provider": "unsplash",
                    "source_type": "api",
                    "local_path": None,
                    "source_url": (r.get("links") or {}).get("download"),
                    "license": "unsplash",
                    "attribution": f"Photo by {(r.get('user') or {}).get('name', 'Unknown')} on Unsplash",
                    "keywords": [w for w in (r.get("alt_description") or "").split() if w],
                    "width": r.get("width", 0),
                    "height": r.get("height", 0),
                }
            )
        return candidates
