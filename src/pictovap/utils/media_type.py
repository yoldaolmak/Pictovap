"""MIME types for CMS media uploads."""

import mimetypes


def upload_content_type(filename: str) -> str:
    """Recognize pipeline WebP output even on minimal Linux images."""
    if filename.lower().endswith(".webp"):
        return "image/webp"
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"
