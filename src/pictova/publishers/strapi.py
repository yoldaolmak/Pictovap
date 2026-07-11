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
from typing import Any, Dict, List

import requests

from pictova.core.primitives import CMSPlacement
from pictova.utils.config import load_project_env

load_project_env()


class StrapiPublisher:
    """Upload and attach images to Strapi CMS via the REST API.

    Usage::

        pub = StrapiPublisher()
        result = pub.upload_media(
            file_path="path/to/photo.webp",
            title="Riverside Park",
            alt_text="Morning mist over the riverside park",
            caption="Calm waters at the riverside park.",
        )
        media_id = result["media_id"]  # Strapi numeric file ID
        media_url = result["url"]
    """

    def __init__(
        self,
        strapi_url: str | None = None,
        api_token: str | None = None,
        *,
        content_type: str = "articles",
        field_name: str = "cover",
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
        # Defaults used by place(); a single Strapi content-type field can only
        # ever hold one media reference at a time (see place() docstring).
        self._content_type = content_type
        self._field_name = field_name

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

    # ------------------------------------------------------------------
    # Public interface (CMSAdapter)
    # ------------------------------------------------------------------

    def place(self, placement: CMSPlacement) -> Dict[str, Any]:
        """Execute a CMS-agnostic placement plan against this Strapi entry.

        `placement.article_id` is interpreted as the Strapi entry ID.

        Strapi content-types are user-defined, so this generic adapter only
        knows about a single media field (`field_name`, default ``"cover"``)
        on a single content-type (`content_type`, default ``"articles"``).
        Every image is uploaded to the media library regardless, but only
        one placement can end up attached to that field — if `placement`
        contains more than one instruction, every upload still happens and
        succeeds, but only the *last* `attach_to_post` call wins the field,
        and the earlier ones are reported back as warnings rather than
        silently dropped. Projects with a gallery/repeatable media field
        should subclass this adapter and override `place()`.
        """
        placed: List[Dict[str, Any]] = []
        failed: List[Dict[str, Any]] = []
        warnings: List[str] = []

        uploads: List[Dict[str, Any]] = []
        for instr in placement.placements:
            upload = self.upload_media(
                file_path=instr.output_path,
                title=instr.slot_id,
                alt_text=instr.alt_text,
                caption=instr.caption,
            )
            if not upload.get("success"):
                failed.append({"slot_id": instr.slot_id, "stage": "upload", "error": upload.get("error")})
                continue
            uploads.append({"instr": instr, "upload": upload})

        if len(uploads) > 1:
            warnings.append(
                f"{len(uploads)} images uploaded, but StrapiPublisher only attaches one media field "
                f"({self._content_type}.{self._field_name}) per entry; only the last placement below "
                "will actually be attached to the entry."
            )

        for entry in uploads:
            instr, upload = entry["instr"], entry["upload"]
            attach = self.attach_to_post(
                upload["media_id"],
                placement.article_id,
                content_type=self._content_type,
                field_name=self._field_name,
            )
            if not attach.get("success"):
                failed.append({"slot_id": instr.slot_id, "stage": "attach", "error": attach.get("error")})
                continue
            placed.append({
                "slot_id": instr.slot_id,
                "media_id": upload["media_id"],
                "url": upload.get("url"),
                "image_role": instr.image_role,
            })

        return {"placed": placed, "failed": failed, "warnings": warnings}


__all__ = ["StrapiPublisher"]
