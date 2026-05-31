#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path

from yo_metadata_generator import clean_text, topic_visual_detail
from yo_wp_uploader import YOWordPressUploader

ROOT = Path('/YOOS-VIL')
LOG_DIR = ROOT / 'ops_logs' / 'media_meta_repair'
BACKUP_DIR = ROOT / 'ops_backups' / 'media_meta_repair'
POST_IDS = [264462, 264463, 264486, 264459, 264458, 264585, 249223, 264454, 264532, 264525, 264528, 152168]
IMG_RE = re.compile(r'<!-- wp:image\b.*?<!-- /wp:image -->', re.S | re.I)


def strip_tags(value: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html.unescape(value or ''))).strip()


def media_ids(content: str) -> list[int]:
    ids = []
    for raw in re.findall(r'wp-image-(\d+)', content):
        mid = int(raw)
        if mid not in ids:
            ids.append(mid)
    return ids


def meta_for(title: str, index: int) -> dict:
    detail = topic_visual_detail(title)
    variants = ['ana görsel', 'kontrol listesi', 'belge detayı', 'seyahat planı', 'hazırlık notu']
    variant = variants[(index - 1) % len(variants)]
    alt = clean_text(f'{title} için {detail}', limit=125)
    media_title = clean_text(f'{title} {variant}', limit=60)
    caption = clean_text(f'{title} içeriğini destekleyen {detail}', limit=180)
    description = clean_text(f'{title} yazısında kullanılan {detail} odaklı görsel.', limit=300)
    return {'alt': alt, 'title': media_title, 'caption': caption, 'description': description}


def canonical_block(block: str, mid: int, meta: dict) -> str:
    src = re.search(r'<img[^>]+src="([^"]+)"', block, re.I)
    url = html.escape(src.group(1), quote=True) if src else ''
    alt = html.escape(meta['alt'], quote=True)
    caption = html.escape(meta['caption'])
    return (
        f'<!-- wp:image {{"id":{mid},"sizeSlug":"full","linkDestination":"none"}} -->\n'
        f'<figure class="wp-block-image size-full"><img src="{url}" alt="{alt}" class="wp-image-{mid}" />'
        f'<figcaption class="wp-element-caption">{caption}</figcaption></figure>\n'
        '<!-- /wp:image -->'
    )


def repair_post(uploader: YOWordPressUploader, post_id: int) -> dict:
    post = uploader.fetch_post_context(post_id)
    title = strip_tags(post.get('title', ''))
    content = post.get('content_raw', '') or ''
    ids = media_ids(content)
    if not ids:
        return {'post_id': post_id, 'status': 'skipped', 'reason': 'no_images'}

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}-post-{post_id}.html"
    backup.write_text(content)

    meta_by_id = {mid: meta_for(title, i) for i, mid in enumerate(ids, 1)}
    media_results = []
    for mid, meta in meta_by_id.items():
        endpoint = f'{uploader.base_url}/wp-json/wp/v2/media/{mid}'
        resp = uploader.session.post(endpoint, json={
            'alt_text': meta['alt'],
            'title': meta['title'],
            'caption': meta['caption'],
            'description': meta['description'],
        }, timeout=30)
        media_results.append({'id': mid, 'ok': resp.status_code < 400, 'status': resp.status_code})

    def replace(match: re.Match[str]) -> str:
        block = match.group(0)
        got = re.search(r'wp-image-(\d+)', block)
        if not got:
            return block
        mid = int(got.group(1))
        meta = meta_by_id.get(mid)
        if not meta:
            return block
        return canonical_block(block, mid, meta)

    new_content = IMG_RE.sub(replace, content)
    post_resp = uploader.session.post(f'{uploader.base_url}/wp-json/wp/v2/posts/{post_id}', json={'content': new_content}, timeout=60)
    return {
        'post_id': post_id,
        'title': title,
        'status': 'updated' if post_resp.status_code < 400 and all(x['ok'] for x in media_results) else 'failed',
        'images': len(ids),
        'media': media_results,
        'backup': str(backup),
        'post_status': post_resp.status_code,
    }


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    uploader = YOWordPressUploader(site='yoldaolmak')
    with log_path.open('a') as log:
        for post_id in POST_IDS:
            result = repair_post(uploader, post_id)
            print(json.dumps(result, ensure_ascii=False))
            log.write(json.dumps(result, ensure_ascii=False) + '\n')
    print(f'log={log_path}')


if __name__ == '__main__':
    main()
