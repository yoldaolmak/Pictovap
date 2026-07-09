"""
Ghost CMS publisher adapter.

Uses Ghost Admin API v3+ (Content API + Admin API) to upload images
and attach them to posts.

Requires the following environment variables:
    GHOST_URL           — e.g. https://myblog.ghost.io
    GHOST_ADMIN_API_KEY — Format: <id>:<secret>  (from Ghost Admin → Integrations)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from typing import Any, Dict

import requests

from pictova.utils.config import load_project_env

load_project_env()


def _get_jwt_token(api_key: str) -> str:
    """Generate a short-lived JWT for Ghost Admin API authentication.

    Ghost Admin API keys are in the format  <id>:<secret>
    where id is the kid header and secret is a hex-encoded 64-byte HMAC key.
    """
    key_id, secret = api_key.split(":", 1)
    iat = int(time.time())
    exp = iat + 5 * 60  # 5 minutes validity

    header = {"alg": "HS256", "kid": key_id, "typ": "JWT"}
    payload = {"iat": iat, "exp": exp, "aud": "/admin/"}

    def _b64(data: bytes) -> str:
        import base64
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    h = _b64(json.dumps(header, separators=(",", ":")).encode())
    p = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{h}.{p}".encode()

    sig = hmac.new(bytes.fromhex(secret), signing_input, hashlib.sha256).digest()
    return f"{h}.{p}.{_b64(sig)}"


class GhostPublisher:
    """Upload and attach images to Ghost CMS posts via the Admin API.

    Usage::

        pub = GhostPublisher()
        result = pub.upload_media(
            file_path="path/to/photo.webp",
            title="Akyaka Beach",
            alt_text="Turquoise water at Akyaka beach",
        )
        media_url = result["url"]
    """

    def __init__(
        self,
        ghost_url: str | None = None,
        admin_api_key: str | None = None,
    ) -> None:
        self.base_url = (ghost_url or os.environ.get("GHOST_URL", "")).rstrip("/")
        self._admin_key = admin_api_key or os.environ.get("GHOST_ADMIN_API_KEY", "")
        if not self.base_url or not self._admin_key:
            raise ValueError(
                "GhostPublisher requires GHOST_URL and GHOST_ADMIN_API_KEY "
                "(e.g. set them in your .env file)."
            )
        self._session = requests.Session()

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Ghost {_get_jwt_token(self._admin_key)}"}

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
        """Upload an image to Ghost media library.

        Returns:
            dict with ``success``, ``media_id`` (the CDN url used as id),
            ``url``, ``title``, ``alt_text``.
        """
        file_p = Path(file_path)
        if not file_p.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        upload_url = f"{self.base_url}/ghost/api/admin/images/upload/"
        headers = self._auth_headers()

        try:
            with open(file_path, "rb") as fh:
                resp = self._session.post(
                    upload_url,
                    headers=headers,
                    files={"file": (file_p.name, fh, "image/webp")},
                    data={"purpose": "image", "ref": file_p.name},
                    timeout=30,
                )
            resp.raise_for_status()
            image_url: str = resp.json()["images"][0]["url"]

            return {
                "success": True,
                "media_id": image_url,  # Ghost uses the URL as the media identifier
                "url": image_url,
                "title": title,
                "alt_text": alt_text,
                "file": file_p.name,
            }
        except requests.RequestException as exc:
            return {"success": False, "error": str(exc), "file": file_p.name}

    def attach_to_post(self, media_id: Any, post_id: Any) -> Dict[str, Any]:
        """Insert the uploaded image URL into a Ghost post's mobiledoc/lexical body.

        Ghost does not have a native "attach media to post" endpoint.
        This helper appends a simple image card to the post's content.

        Args:
            media_id: The public CDN URL returned by ``upload_media``.
            post_id:  Ghost post UUID.
        """
        post_url = f"{self.base_url}/ghost/api/admin/posts/{post_id}/"
        headers = {**self._auth_headers(), "Content-Type": "application/json"}

        # Fetch current post to get updated_at (required for optimistic locking)
        try:
            get_resp = self._session.get(post_url, headers=headers, timeout=15)
            get_resp.raise_for_status()
            post_data = get_resp.json()["posts"][0]
            updated_at = post_data["updated_at"]

            # Append image card using Lexical format (Ghost >= 6.x)
            existing_lexical = post_data.get("lexical") or "{}"
            try:
                lexical = json.loads(existing_lexical)
            except (json.JSONDecodeError, TypeError):
                lexical = {}

            nodes = lexical.get("root", {}).get("children", [])
            nodes.append({
                "type": "image",
                "src": str(media_id),
                "width": None,
                "height": None,
                "caption": "",
                "alt": "",
                "cardWidth": "regular",
                "href": "",
                "version": 1,
            })
            if "root" not in lexical:
                lexical["root"] = {"children": nodes, "direction": None, "format": "", "indent": 0, "type": "root", "version": 1}
            else:
                lexical["root"]["children"] = nodes

            update_resp = self._session.put(
                post_url,
                headers=headers,
                json={"posts": [{"lexical": json.dumps(lexical), "updated_at": updated_at}]},
                timeout=20,
            )
            update_resp.raise_for_status()
            return {"success": True, "media_id": media_id, "post_id": post_id}
        except requests.RequestException as exc:
            return {"success": False, "error": str(exc)}

    def fetch_post_context(self, post_id: Any, **kwargs: Any) -> Dict[str, Any]:
        """Fetch title, slug, and raw content for a Ghost post."""
        post_url = f"{self.base_url}/ghost/api/admin/posts/{post_id}/"
        headers = self._auth_headers()
        try:
            resp = self._session.get(post_url, headers=headers, timeout=15)
            resp.raise_for_status()
            post = resp.json()["posts"][0]
            return {
                "title": post.get("title", ""),
                "slug": post.get("slug", ""),
                "content_raw": post.get("html") or post.get("plaintext") or "",
                "tags": [t.get("name", "") for t in post.get("tags", [])],
                "status": post.get("status", ""),
            }
        except requests.RequestException as exc:
            return {"title": "", "slug": "", "content_raw": "", "error": str(exc)}


__all__ = ["GhostPublisher"]
