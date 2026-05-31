#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

from yo_wp_uploader import YOWordPressUploader

POST_ID = 264443
ROOT = Path('/YOOS-VIL')
BACKUP_DIR = ROOT / 'ops_backups' / 'licensed_upload_264443'
VIL = Path('/root/Downloads/VIL')
SOURCES = [
    (VIL / 'yo-licensed-264443-1-airport-security-personal-belongings-tray.jpg', 'kabin-bagaji-guvenlik-tepsisi'),
    (VIL / 'yo-licensed-264443-2-airport-security-luggage-conveyor.jpg', 'kabin-bagaji-xray-konveyor'),
]
HEADING_RE = re.compile(r'(?:<!-- wp:heading(?:\s+\{.*?\})? -->\s*)?<h[23]\b[^>]*>.*?</h[23]>\s*(?:<!-- /wp:heading -->)?', re.S | re.I)
IMG_RE = re.compile(r'<!-- wp:image\b.*?<!-- /wp:image -->\s*', re.S | re.I)


def make_webp(src: Path, slug: str) -> Path:
    out = VIL / f'yo-final-264443-{slug}.webp'
    with Image.open(src) as img:
        img = ImageOps.exif_transpose(img).convert('RGB')
        fitted = ImageOps.fit(img, (1200, 750), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        fitted.save(out, format='WEBP', quality=92, method=6)
    return out


def clean_existing_problem_images(content: str) -> str:
    def repl(match: re.Match[str]) -> str:
        block = match.group(0)
        if not re.search(r'<img[^>]+src="[^"]+"', block, re.I) or not re.search(r'wp-image-\d+|"id"\s*:\s*\d+', block):
            return ''
        return block
    return IMG_RE.sub(repl, content)


def block(media: dict) -> str:
    mid = int(media['media_id'])
    url = html.escape(media['url'], quote=True)
    alt = html.escape(media['alt'], quote=True)
    cap = html.escape(media['caption'])
    return (
        f'<!-- wp:image {{"id":{mid},"sizeSlug":"full","linkDestination":"none"}} -->\n'
        f'<figure class="wp-block-image size-full"><img src="{url}" alt="{alt}" class="wp-image-{mid}" />'
        f'<figcaption class="wp-element-caption">{cap}</figcaption></figure>\n'
        '<!-- /wp:image -->'
    )


def insert_after_headings(content: str, blocks: list[str]) -> str:
    content = clean_existing_problem_images(content).strip() + '\n'
    headings = list(HEADING_RE.finditer(content))
    if not headings:
        return content + '\n\n'.join(blocks) + '\n'
    additions = []
    for i, b in enumerate(blocks):
        additions.append((headings[min(i, len(headings)-1)].end(), '\n\n' + b + '\n\n'))
    out = content
    for pos, add in sorted(additions, reverse=True):
        out = out[:pos].rstrip() + add + out[pos:].lstrip()
    return out.strip() + '\n'


def main() -> None:
    uploader = YOWordPressUploader(site='yoldaolmak')
    post = uploader.fetch_post_context(POST_ID)
    content = post.get('content_raw', '') or ''
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}-post-{POST_ID}.html"
    backup.write_text(content)

    metas = [
        {
            'title': 'Kabin bagajı güvenlik tepsisi',
            'alt': 'Kabin bagajı kuralları için havalimanı güvenlik tepsisindeki kişisel eşyalar',
            'caption': 'Kabin bagajı ve güvenlik kontrolü kurallarını anlatan havalimanı güvenlik tepsisi görseli.',
            'description': 'Kabin bagajı, sıvı kısıtlamaları ve güvenlik kontrolü konularını destekleyen lisanslı DepositPhotos görseli.',
        },
        {
            'title': 'Havalimanı bagaj X-ray konveyörü',
            'alt': 'Kabin bagajı kontrolü için havalimanı X-ray konveyöründeki valizler',
            'caption': 'Havalimanı X-ray kontrolünde kabin bagajı ve valizlerin güvenlikten geçişini gösteren görsel.',
            'description': 'Kabin bagajı yasaklı maddeler ve X-ray güvenlik kontrolü bölümünü destekleyen lisanslı DepositPhotos görseli.',
        },
    ]
    uploaded = []
    for (src, slug), meta in zip(SOURCES, metas):
        if not src.exists():
            raise FileNotFoundError(src)
        webp = make_webp(src, slug)
        result = uploader.upload_media(str(webp), meta['title'], meta['alt'], meta['description'], meta['caption'])
        if not result.get('success'):
            raise RuntimeError(result)
        uploader.attach_to_post(result['media_id'], POST_ID)
        uploaded.append({**result, **meta, 'file': str(webp), 'bytes': webp.stat().st_size})

    new_content = insert_after_headings(content, [block(item) for item in uploaded])
    resp = uploader.session.post(f'{uploader.base_url}/wp-json/wp/v2/posts/{POST_ID}', json={'content': new_content}, timeout=60)
    resp.raise_for_status()
    print(json.dumps({'post_id': POST_ID, 'uploaded': uploaded, 'backup': str(backup), 'post_update': resp.status_code}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
