#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from src.core.yo_wp_uploader import YOWordPressUploader

POST_IDS = [264462, 264463, 264486, 264459, 264458, 264585, 264532, 264525, 264528, 260971]
ROOT = Path('/YOOS-VIL')
BACKUP_DIR = ROOT / 'ops_backups' / 'block_boundary_fix'
IMG_BLOCK_RE = re.compile(r'<!-- wp:image\b.*?<!-- /wp:image -->\s*', re.S | re.I)


def remove_empty_image_blocks(content: str) -> tuple[str, int]:
    removed = 0
    def repl(match: re.Match[str]) -> str:
        nonlocal removed
        block = match.group(0)
        has_src = bool(re.search(r'<img[^>]+src="[^"]+"', block, re.I))
        has_id = bool(re.search(r'wp-image-\d+|"id"\s*:\s*\d+', block))
        if not has_src or not has_id:
            removed += 1
            return ''
        return block
    return IMG_BLOCK_RE.sub(repl, content), removed


def fix_boundaries(content: str) -> tuple[str, int]:
    fixes = 0
    patterns = [
        (re.compile(r'\n\s*<!\s*\n\s*(<!-- wp:image\b)', re.I), '\n\n\\1'),
        (re.compile(r'(<!-- /wp:image -->)\s*\n\s*-- wp:([a-z0-9_-]+)([^\n>]*)-->', re.I), '\\1\n\n<!-- wp:\\2\\3-->'),
        (re.compile(r'(<!-- /wp:image -->)\s*\n\s*-- /wp:([a-z0-9_-]+)\s*-->', re.I), '\\1\n\n<!-- /wp:\\2 -->'),
    ]
    for pattern, repl in patterns:
        content, n = pattern.subn(repl, content)
        fixes += n
    return content, fixes


def main() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    uploader = YOWordPressUploader(site='yoldaolmak')
    for pid in POST_IDS:
        post = uploader.fetch_post_context(pid)
        content = post.get('content_raw', '') or ''
        backup = BACKUP_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}-post-{pid}.html"
        backup.write_text(content)
        new_content, removed_empty = remove_empty_image_blocks(content)
        new_content, boundary_fixes = fix_boundaries(new_content)
        changed = new_content != content
        status = None
        if changed:
            resp = uploader.session.post(f'{uploader.base_url}/wp-json/wp/v2/posts/{pid}', json={'content': new_content}, timeout=60)
            status = resp.status_code
        print(json.dumps({
            'post_id': pid,
            'changed': changed,
            'removed_empty_images': removed_empty,
            'boundary_fixes': boundary_fixes,
            'status': status,
            'backup': str(backup),
        }, ensure_ascii=False))


if __name__ == '__main__':
    main()
