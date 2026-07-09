"""
Strapi CMS publisher adapter.

Supports Strapi v4 and v5 REST API.
Uploads images to the Strapi Media Library and can attach them to any
content-type's rich-text/media field.

Requires the following environment variables:
    STRAPI_URL          — e.g. https://cms.myblog.com
    STRAPI_API_TOKEN    — Full-access API token from Strapi Admin
                          (Settings → API Tokens → Create new token)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

import requests

from pictova.utils.config import load_project_env

load_project_env()


class StrapiPublisher:
    """Upload and attach images to Strapi CMS via the REST API.

    Usage::

        pub = StrapiPublisher()
        result = pub.upload_media(
            file_path="path/to/photo.webp",
            title="Akyaka Beach",
            alt_text="Turquoise water at Akyaka beach",
            caption="Calm waters at Akyaka, Muğla.",
        )
        media_id = result["media_id"]  # Strapi numeric file ID
        media_url = result["url"]
    """

    def __init__(
        self,
        strapi_url: str | None = None,
        api_token: str | None = None,
    ) -> None:
        self.base_url = (strapi_url or os.environ.get("STRAPI_URL", "")).rstrip("/")
        self._token = api_token or os.environ.get("STRAPI_API_TOKEN", "")
        if not self.base_url or not self._token:
            raise ValueError(
                "StrapiPublisher requires STRAPI_URL and STRAPI_API_TOKEN "
                "(set them in your .env file or pass directly)."
            )
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {self._token}"})

    # ------------------------------------------------------------------
    # Public interface (PublisherProtocol)
    # ------------------------------------------------------------------

    def upload_media(
        self,
        file_path: str,
        title: str,
        alt_text: str,
        description: str = "",
        caption: str = "",
    ) -> Dict[str, Any]:
        """Upload an image to the Strapi Media Library.

        Uses Strapi's ``/api/upload`` endpoint which accepts ``multipart/form-data``.

        Returns:
            dict with ``success``, ``media_id`` (Strapi numeric file ID),
            ``url``, ``title``, ``alt_text``.
        """
        file_p = Path(file_path)
        if not file_p.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        upload_url = f"{self.base_url}/api/upload"

        # Strapi v4/v5: fileInfo is passed as JSON string in a separate field
        file_info = json.dumps({
            "name": file_p.stem,
            "alternativeText": alt_text,
            "caption": caption,
        })

        try:
            with open(file_path, "rb") as fh:
                resp = self._session.post(
                    upload_url,
                    files={"files": (file_p.name, fh, "image/webp")},
                    data={"fileInfo": file_info},
                    timeout=30,
                )
            resp.raise_for_status()
            uploaded = resp.json()
            if isinstance(uploaded, list):
                uploaded = uploaded[0]

            media_id = uploaded.get("id")
            # Strapi v4 returns relative URLs; build absolute
            raw_url: str = uploaded.get("url", "")
            if raw_url.startswith("/"):
                raw_url = f"{self.base_url}{raw_url}"

            return {
                "success": True,
                "media_id": media_id,
                "url": raw_url,
                "title": title,
                "alt_text": alt_text,
                "file": file_p.name,
            }
        except requests.RequestException as exc:
            return {"success": False, "error": str(exc), "file": file_p.name}

    def attach_to_post(
        self,
        media_id: Any,
        post_id: Any,
        *,
        content_type: str = "articles",
        field_name: str = "cover",
    ) -> Dict[str, Any]:
        """Attach a media file to a Strapi content entry.

        Args:
            media_id:     Strapi numeric file ID.
            post_id:      Strapi entry ID.
            content_type: Strapi collection-type API path (e.g. 'articles', 'posts').
            field_name:   The media field on the content-type (e.g. 'cover', 'gallery').
        """
        update_url = f"{self.base_url}/api/{content_type}/{post_id}"
        payload = {"data": {field_name: media_id}}
        try:
            resp = self._session.put(update_url, json=payload, timeout=20)
            resp.raise_for_status()
            return {"success": True, "media_id": media_id, "post_id": post_id}
        except requests.RequestException as exc:
            return {"success": False, "error": str(exc)}

    def fetch_post_context(
        self,
        post_id: Any,
        *,
        content_type: str = "articles",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Fetch title, slug, and content for a Strapi entry.

        Args:
            post_id:      Strapi entry ID.
            content_type: Strapi collection-type API path (e.g. 'articles').
        """
        fetch_url = f"{self.base_url}/api/{content_type}/{post_id}"
        try:
            resp = self._session.get(
                fetch_url,
                params={"populate": "cover,tags"},
                timeout=15,
            )
            resp.raise_for_status()
            attrs = resp.json().get("data", {}).get("attributes", {})
            return {
                "title": attrs.get("title", ""),
                "slug": attrs.get("slug", ""),
                "content_raw": attrs.get("content") or attrs.get("body") or "",
                "tags": [
                    t.get("attributes", {}).get("name", "")
                    for t in ((attrs.get("tags") or {}).get("data") or [])
                ],
                "status": attrs.get("publishedAt") and "published" or "draft",
            }
        except requests.RequestException as exc:
            return {"title": "", "slug": "", "content_raw": "", "error": str(exc)}


__all__ = ["StrapiPublisher"]
