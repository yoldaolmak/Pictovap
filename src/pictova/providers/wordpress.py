"""Canonical WordPress provider exports."""

from __future__ import annotations

from pictova.services.wordpress import YOWordPressUploader, fetch_post_context, upload_images_batch


def guard_post_media(
    post_id: int,
    *,
    site: str = "yoldaolmak",
    repair: bool = False,
    adopt: bool = False,
    media_ids: list[int] | None = None,
) -> dict:
    uploader = YOWordPressUploader(site=site)
    return uploader.guard_post_media(
        post_id,
        repair=repair,
        adopt=adopt,
        media_ids=media_ids,
    )


__all__ = ["YOWordPressUploader", "fetch_post_context", "guard_post_media", "upload_images_batch"]
