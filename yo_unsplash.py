#!/usr/bin/env python3
"""YO OS Unsplash downloader."""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
from typing import Dict, List

import requests

from src.utils.config import get_vil_dir, load_project_env

load_project_env()


class YOUnsplashDownloader:
    """Download travel photos from Unsplash by query."""

    def __init__(self):
        self.access_key = os.environ.get("UNSPLASH_ACCESS_KEY")
        self.api_url = os.environ.get("UNSPLASH_API_URL", "https://api.unsplash.com")
        self.vil_dir = get_vil_dir()
        self.vil_dir.mkdir(parents=True, exist_ok=True)
        if not self.access_key:
            raise ValueError("UNSPLASH_ACCESS_KEY not set")

    def search(self, query: str, count: int = 5, page: int = 1) -> List[Dict]:
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
                    "timestamp": datetime.now().isoformat(),
                }
                filepath.with_suffix(".json").write_text(
                    json.dumps(metadata, indent=2, ensure_ascii=False)
                )
                downloaded.append(str(filepath))
            except Exception:
                continue
        return downloaded
