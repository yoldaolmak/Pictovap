#!/usr/bin/env python3
import json
import re
from src.core.yo_wp_uploader import YOWordPressUploader

POST_IDS = [264462, 264463, 264486, 264459, 264458, 264585, 249223, 264454, 264532, 264525, 264528, 152168]
BAD = [' kap da ', ' nas l ', ' g venlik', 'yo cycle', 'depositphotos']
IMG_RE = re.compile(r'<!-- wp:image\b.*?<!-- /wp:image -->', re.S | re.I)
HEADING_RE = re.compile(r'(?:<!-- wp:heading.*?-->)?\s*<h[23]\b[^>]*>.*?</h[23]>\s*(?:<!-- /wp:heading -->)?', re.S | re.I)

u = YOWordPressUploader(site='yoldaolmak')

def media_meta(mid):
    r = u.session.get(f'{u.base_url}/wp-json/wp/v2/media/{mid}?context=edit', timeout=30)
    if r.status_code >= 400:
        return '', '', ''
    data = r.json()
    return data.get('alt_text') or '', data.get('title', {}).get('raw') or data.get('title', {}).get('rendered') or '', data.get('caption', {}).get('raw') or data.get('caption', {}).get('rendered') or ''

for pid in POST_IDS:
    post = u.fetch_post_context(pid)
    content = post.get('content_raw', '') or ''
    imgs = IMG_RE.findall(content)
    ids = list(dict.fromkeys(int(x) for x in re.findall(r'wp-image-(\d+)', content)))
    headings = list(HEADING_RE.finditer(content))
    near_heading = 0
    for block in imgs:
        start = content.find(block)
        before = content[max(0, start - 700):start]
        if re.search(r'<h[23]\b[^>]*>.*?</h[23]>\s*(?:<!-- /wp:heading -->)?\s*$', before, re.S | re.I):
            near_heading += 1
    bad_meta = []
    for mid in ids:
        alt, title, cap = media_meta(mid)
        blob = f' {alt} {title} {cap} '.lower()
        if any(token in blob for token in BAD):
            bad_meta.append(mid)
    print(json.dumps({
        'post_id': pid,
        'images': len(ids),
        'image_blocks': len(imgs),
        'headings': len(headings),
        'near_heading': near_heading,
        'auto_region': '<!-- yo:auto-media:start -->' in content,
        'bad_meta': bad_meta,
        'canonical_img': all(' />' in b for b in imgs),
    }, ensure_ascii=False))
