#!/usr/bin/env python3
"""
YO OS Unsplash Downloader — Download travel photos from Unsplash by query
"""

import os
import requests
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json

from settings import get_vil_dir, load_project_env

load_project_env()


class YOUnsplashDownloader:
    """Download images from Unsplash Foto API"""

    def __init__(self):
        self.access_key = os.environ.get("UNSPLASH_ACCESS_KEY")
        self.api_url = os.environ.get("UNSPLASH_API_URL", "https://api.unsplash.com")
        self.vil_dir = get_vil_dir()
        self.vil_dir.mkdir(parents=True, exist_ok=True)

        if not self.access_key:
            raise ValueError("UNSPLASH_ACCESS_KEY not set")

    def search(self, query: str, count: int = 5, page: int = 1) -> List[Dict]:
        """Search for images on Unsplash

        Args:
            query: search query (e.g. "zadar sea")
            count: number of images to fetch
            page: page number for pagination

        Returns:
            list of image data dicts
        """
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

            data = resp.json()
            results = data.get("results", [])

            print(f"🔍 Unsplash search: '{query}'")
            print(f"  📊 Found: {data.get('total', 0)} results")
            print(f"  📄 Returned: {len(results)} images")

            return results

        except Exception as e:
            print(f"  ✗ Search error: {e}")
            return []

    def download(
        self,
        query: str,
        count: int = 5,
        naming_template: str = "{location}-{number}",
    ) -> List[str]:
        """Search and download images from Unsplash

        Args:
            query: search query
            count: number of images to download
            naming_template: filename template (e.g. "zadar-{number}")

        Returns:
            list of saved file paths
        """
        results = self.search(query, count=count)

        if not results:
            print(f"  ✗ No images found for '{query}'")
            return []

        downloaded = []

        for i, result in enumerate(results[:count], 1):
            try:
                # Get download URL
                download_url = result["links"]["download"]
                photo_id = result["id"]
                user_name = result["user"]["username"]
                alt_text = result.get("alt_description", "Unsplash photo")

                # Generate filename
                location = query.split()[0].lower()  # First word
                filename = naming_template.format(location=location, number=i).replace(
                    " ", "-"
                )
                if not filename.endswith((".jpg", ".png", ".webp")):
                    filename += ".jpg"

                filepath = self.vil_dir / filename

                print(f"\n  📥 [{i}/{len(results[:count])}] {filename}")
                print(f"     ID: {photo_id} | By: {user_name}")

                # Download with auth
                headers = {"Authorization": f"Client-ID {self.access_key}"}
                resp = requests.get(download_url, headers=headers, timeout=30)
                resp.raise_for_status()

                # Save file
                with open(filepath, "wb") as f:
                    f.write(resp.content)

                size_mb = filepath.stat().st_size / (1024 * 1024)
                print(f"     ✓ Saved: {size_mb:.1f} MB")

                # Log metadata
                metadata = {
                    "source": "unsplash",
                    "photo_id": photo_id,
                    "user": user_name,
                    "query": query,
                    "alt": alt_text,
                    "download_url": download_url,
                    "timestamp": datetime.now().isoformat(),
                }

                meta_file = filepath.with_suffix(".json")
                with open(meta_file, "w") as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)

                downloaded.append(str(filepath))

            except Exception as e:
                print(f"     ✗ Error: {str(e)[:100]}")

        print(f"\n  ✅ Downloaded: {len(downloaded)}/{len(results[:count])} images")
        return downloaded


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: yo_unsplash.py '<query>' [count] [template]")
        print("Example: yo_unsplash.py 'zadar sea' 5")
        print("Example: yo_unsplash.py 'istanbul cityscape' 3 'istanbul-{number}'")
        sys.exit(1)

    query = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    template = sys.argv[3] if len(sys.argv) > 3 else "{location}-{number}"

    downloader = YOUnsplashDownloader()
    downloaded = downloader.download(query, count=count, naming_template=template)

    if downloaded:
        print(f"\n📂 Files saved to: {downloader.vil_dir}")
        for f in downloaded:
            print(f"   - {Path(f).name}")


if __name__ == "__main__":
    main()
