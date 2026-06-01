#!/usr/bin/env python3
"""Gutenberg block helpers for YOOS-VIL WordPress content edits."""

from __future__ import annotations

import html
from typing import Iterable, Mapping


def image_block(item: Mapping[str, object]) -> str:
    """Return an editor-safe native Gutenberg core/image block for galleries.

    Required item keys: media_id, url, alt. Captions stay in WordPress media
    metadata; this gallery shape mirrors existing valid site content and avoids
    Gutenberg invalid-block recovery errors.
    """
    media_id = int(item["media_id"])
    url = html.escape(str(item.get("url", "")), quote=True)
    alt = html.escape(str(item.get("alt", "")), quote=True)
    return (
        f'<!-- wp:image {{"id":{media_id},"className":"size-large"}} -->\n'
        f'<figure class="wp-block-image size-large"><img src="{url}" alt="{alt}" class="wp-image-{media_id}"/></figure>\n'
        '<!-- /wp:image -->'
    )


def native_gallery_block(items: Iterable[Mapping[str, object]], *, columns: int = 2) -> str:
    """Return an editor-safe native Gutenberg core/gallery block.

    WordPress 7.0 on yoldaolmak validates this saved shape:
    - gallery attrs: {"linkTo":"none"}
    - wrapper: columns-default is-cropped
    - nested image attrs: {"id": <id>, "className": "size-large"}
    Passing `columns` is kept for API compatibility but intentionally ignored
    to match the site's existing valid native galleries.
    """
    rows = list(items)
    inner = "\n\n".join(image_block(item) for item in rows)
    return (
        '<!-- wp:gallery {"linkTo":"none"} -->\n'
        '<figure class="wp-block-gallery has-nested-images columns-default is-cropped">'
        f'{inner}'
        '</figure>\n'
        '<!-- /wp:gallery -->'
    )
