"""
Base publisher interface.

All CMS publisher adapters must implement this protocol so the engine
can treat any CMS target identically via duck-typing.
"""

from __future__ import annotations

from typing import Any, Dict, Protocol


class PublisherProtocol(Protocol):
    """Contract that every CMS publisher adapter must satisfy."""

    def upload_media(
        self,
        file_path: str,
        title: str,
        alt_text: str,
        description: str = "",
        caption: str = "",
    ) -> Dict[str, Any]:
        """Upload a local image file to the CMS media library.

        Returns a dict with at least:
            - success (bool)
            - media_id (str | int)
            - url (str)  — publicly accessible CDN URL
            - error (str, only on failure)
        """
        ...

    def attach_to_post(self, media_id: Any, post_id: Any) -> Dict[str, Any]:
        """Associate an already-uploaded media item with a post/article.

        Returns a dict with at least:
            - success (bool)
            - error (str, only on failure)
        """
        ...

    def fetch_post_context(self, post_id: Any, **kwargs: Any) -> Dict[str, Any]:
        """Fetch title, slug, content, and other metadata for a given post.

        Returns a dict with at least:
            - title (str)
            - slug (str)
            - content_raw (str)
        """
        ...
