#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

from yo_wp_uploader import YOWordPressUploader

POST_ID = 264443
OLD_IDS = [264702, 264703]
ROOT = Path('/YOOS-VIL')
VIL = Path('/root/Downloads/VIL')
BACKUP_DIR = ROOT / 'ops_backups' / 'clean_public_filenames_264443'
WP_PATH = Path('/home/yoldaolmak/public_html')
SOURCES = [
    (VIL / 'yo-licensed-264443-1-airport-security-personal-belongings-tray.jpg', 'kabin-bagaji-guvenlik-tepsisi.webp', {
        'title': 'Kabin bagajı güvenlik tepsisi',
        'alt': 'Kabin bagajı kuralları için havalimanı güvenlik tepsisindeki kişisel eşyalar',
        'caption': 'Kabin bagajı ve güvenlik kontrolü kurallarını anlatan havalimanı güvenlik tepsisi görseli.',
        'description': 'Kabin bagajı, sıvı kısıtlamaları ve güvenlik kontrolü konularını destekleyen lisanslı DepositPhotos görseli.',
    }),
    (VIL / 'yo-licensed-264443-2-airport-security-luggage-conveyor.jpg', 'kabin-bagaji-xray-konveyor.webp', {
        'title': 'Havalimanı bagaj X-ray konveyörü',
        'alt': 'Kabin bagajı kontrolü için havalimanı X-ray konveyöründeki valizler',
        'caption': 'Havalimanı X-ray kontrolünde kabin bagajı ve valizlerin güvenlikten geçişini gösteren görsel.',
        'description': 'Kabin bagajı yasaklı maddeler ve X-ray güvenlik kontrolü bölümünü destekleyen lisanslı DepositPhotos görseli.',
    }),
]
IMG_RE = re.compile(r'<!-- wp:image\b.*?<!-- /wp:image -->\s*', re.S | re.I)
HEADING_RE = re.compile(r'(?:<!-- wp:heading(?:\s+\{.*?\})? -->\s*)?<h[23]\b[^>]*>.*?</h[23]>\s*(?:<!-- /wp:heading -->)?', re.S | re.I)


def wp(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(['wp', *args, '--allow-root'], cwd=str(WP_PATH), text=True, capture_output=True, check=check)


def make_clean_webp(src: Path, filename: str) -> Path:
    out = VIL / filename
    with Image.open(src) as img:
        img = ImageOps.exif_transpose(img).convert('RGB')
        fitted = ImageOps.fit(img, (1200, 750), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        fitted.save(out, format='WEBP', quality=92, method=6)
    return out


def image_block(item: dict) -> str:
    mid = int(item['media_id'])
    url = html.escape(item['url'], quote=True)
    alt = html.escape(item['alt'], quote=True)
    caption = html.escape(item['caption'])
    return (
        f'<!-- wp:image {{"id":{mid},"sizeSlug":"full","linkDestination":"none"}} -->\n'
        f'<figure class="wp-block-image size-full"><img src="{url}" alt="{alt}" class="wp-image-{mid}" />'
        f'<figcaption class="wp-element-caption">{caption}</figcaption></figure>\n'
        '<!-- /wp:image -->'
    )


def insert_blocks(content: str, blocks: list[str]) -> str:
    clean = IMG_RE.sub('', content).strip() + '\n'
    headings = list(HEADING_RE.finditer(clean))
    if not headings:
        return clean + '\n\n'.join(blocks) + '\n'
    out = clean
    inserts = [(headings[min(i, len(headings) - 1)].end(), '\n\n' + block + '\n\n') for i, block in enumerate(blocks)]
    for pos, addition in sorted(inserts, reverse=True):
        out = out[:pos].rstrip() + addition + out[pos:].lstrip()
    return out.strip() + '\n'


def main() -> None:
    uploader = YOWordPressUploader(site='yoldaolmak')
    post = uploader.fetch_post_context(POST_ID)
    content = post.get('content_raw', '') or ''
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}-post-{POST_ID}.html"
    backup.write_text(content)

    uploaded = []
    for src, filename, meta in SOURCES:
        webp = make_clean_webp(src, filename)
        result = uploader.upload_media(str(webp), meta['title'], meta['alt'], meta['description'], meta['caption'])
        if not result.get('success'):
            raise RuntimeError(result)
        uploader.attach_to_post(result['media_id'], POST_ID)
        uploaded.append({**result, **meta, 'file': str(webp), 'bytes': webp.stat().st_size})

    new_content = insert_blocks(content, [image_block(item) for item in uploaded])
    resp = uploader.session.post(f'{uploader.base_url}/wp-json/wp/v2/posts/{POST_ID}', json={'content': new_content}, timeout=60)
    resp.raise_for_status()

    deleted = []
    for old_id in OLD_IDS:
        got = wp(['post', 'delete', str(old_id), '--force'], check=False)
        deleted.append({'id': old_id, 'ok': got.returncode == 0, 'stderr': got.stderr[-200:]})

    print(json.dumps({'post_id': POST_ID, 'uploaded': uploaded, 'deleted_old': deleted, 'backup': str(backup)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
