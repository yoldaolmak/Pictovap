"""Publishing exports."""

from __future__ import annotations

from typing import Any, Dict, List

from src.services.wordpress import fetch_post_context, upload_images_batch


def publish_processed_images(
    *,
    site: str,
    post_id: int,
    processed_images: List[str],
    metadata_dict: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    return upload_images_batch(
        image_files=processed_images,
        metadata_dict=metadata_dict,
        post_id=post_id,
        site=site,
    )


__all__ = ["fetch_post_context", "publish_processed_images", "upload_images_batch"]
