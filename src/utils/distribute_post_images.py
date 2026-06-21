#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path

from src.core.yo_wp_uploader import YOWordPressUploader

ROOT = Path('/YOOS-VIL')
BACKUP_DIR = ROOT / 'ops_backups' / 'manual_distribute_images'
IMG_RE = re.compile(r'<!-- wp:image\b.*?<!-- /wp:image -->\s*', re.S | re.I)
HEADING_RE = re.compile(r'(?:<!-- wp:heading(?:\s+\{.*?\})? -->\s*)?<h(?P<level>[23])\b[^>]*>(?P<html>.*?)</h(?P=level)>\s*(?:<!-- /wp:heading -->)?', re.S | re.I)

def strip(value: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html.unescape(value or ''))).strip()

def media_record(u, mid: int) -> dict:
    r = u.session.get(f'{u.base_url}/wp-json/wp/v2/media/{mid}?context=edit', timeout=30)
    r.raise_for_status()
    data = r.json()
    src = data.get('source_url') or data.get('guid', {}).get('rendered') or ''
    alt = data.get('alt_text') or ''
    cap = data.get('caption', {}).get('raw') or data.get('caption', {}).get('rendered') or ''
    return {'id': mid, 'url': src, 'alt': strip(alt), 'caption': strip(cap)}

def block(m: dict) -> str:
    mid = int(m['id'])
    url = html.escape(m['url'], quote=True)
    alt = html.escape(m['alt'], quote=True)
    cap = html.escape(m['caption'])
    return f'<!-- wp:image {{"id":{mid},"sizeSlug":"full","linkDestination":"none"}} -->\n<figure class="wp-block-image size-full"><img src="{url}" alt="{alt}" class="wp-image-{mid}" /><figcaption class="wp-element-caption">{cap}</figcaption></figure>\n<!-- /wp:image -->'

def distribute(content: str, blocks: list[str]) -> str:
    clean = IMG_RE.sub('', content).strip() + '\n'
    headings = list(HEADING_RE.finditer(clean))
    if not headings:
        return clean + '\n\n'.join(blocks) + '\n'
    inserts = []
    used = set()
    for i, b in enumerate(blocks):
        idx = min(i, len(headings) - 1)
        while idx in used and idx + 1 < len(headings):
            idx += 1
        used.add(idx)
        inserts.append((headings[idx].end(), '\n\n' + b + '\n\n'))
    out = clean
    for pos, add in sorted(inserts, reverse=True):
        out = out[:pos].rstrip() + add + out[pos:].lstrip()
    return out.strip() + '\n'

def repair(post_id: int, media_ids: list[int]) -> dict:
    u = YOWordPressUploader(site='yoldaolmak')
    post = u.fetch_post_context(post_id)
    content = post.get('content_raw', '') or ''
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}-post-{post_id}.html"
    backup.write_text(content)
    media = [media_record(u, mid) for mid in media_ids]
    new_content = distribute(content, [block(m) for m in media])
    resp = u.session.post(f'{u.base_url}/wp-json/wp/v2/posts/{post_id}', json={'content': new_content}, timeout=60)
    return {'post_id': post_id, 'media_ids': media_ids, 'status': resp.status_code, 'backup': str(backup)}

if __name__ == '__main__':
    print(json.dumps(repair(260971, [264696, 264697, 264698, 264699]), ensure_ascii=False))
