#!/usr/bin/env python3
import html
import json
import re
from src.core.yo_wp_uploader import YOWordPressUploader

POST_IDS = [264462, 264463, 264486, 264459, 264458, 264585, 249223, 264454, 264532, 264525, 264528, 152168]
BAD = [' kap da ', ' nas l ', ' g venlik', 'yo cycle', 'depositphotos']
IMG_BLOCK_RE = re.compile(r'<!-- wp:image\b.*?<!-- /wp:image -->', re.S | re.I)
HEADING_RE = re.compile(r'(?:<!-- wp:heading.*?-->)?\s*<h(?P<level>[23])\b[^>]*>(?P<html>.*?)</h(?P=level)>\s*(?:<!-- /wp:heading -->)?', re.S | re.I)

def strip(value):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html.unescape(value or ''))).strip()

u = YOWordPressUploader(site='yoldaolmak')

for pid in POST_IDS:
    post = u.fetch_post_context(pid)
    content = post.get('content_raw', '') or ''
    heading_events = [(m.start(), m.end(), strip(m.group('html'))) for m in HEADING_RE.finditer(content)]
    image_blocks = [(m.start(), m.group(0)) for m in IMG_BLOCK_RE.finditer(content)]
    image_ids = []
    placements = []
    for pos, block in image_blocks:
        id_match = re.search(r'wp-image-(\d+)', block)
        mid = int(id_match.group(1)) if id_match else None
        if mid and mid not in image_ids:
            image_ids.append(mid)
        prev = [h for h in heading_events if h[1] <= pos]
        next_h = [h for h in heading_events if h[0] > pos]
        prev_heading = prev[-1][2] if prev else ''
        next_heading = next_h[0][2] if next_h else ''
        between = content[(prev[-1][1] if prev else 0):pos] if prev else content[:pos]
        placements.append({
            'id': mid,
            'after_heading': prev_heading[:90],
            'before_next_heading': next_heading[:90],
            'paragraph_gap': len(re.findall(r'<!-- wp:paragraph\b', between, flags=re.I)),
        })
    bad_meta = []
    meta_samples = []
    for mid in image_ids:
        r = u.session.get(f'{u.base_url}/wp-json/wp/v2/media/{mid}?context=edit', timeout=30)
        if r.status_code >= 400:
            bad_meta.append({'id': mid, 'error': r.status_code})
            continue
        data = r.json()
        alt = data.get('alt_text') or ''
        title = data.get('title', {}).get('raw') or data.get('title', {}).get('rendered') or ''
        caption = data.get('caption', {}).get('raw') or data.get('caption', {}).get('rendered') or ''
        blob = f' {alt} {title} {caption} '.lower()
        if any(token in blob for token in BAD):
            bad_meta.append({'id': mid, 'alt': alt, 'title': title})
        meta_samples.append({'id': mid, 'alt': alt[:110], 'title': strip(title)[:80]})
    unique_headings = len({p['after_heading'] for p in placements if p['after_heading']})
    expected = 4 if len(heading_events) >= 2 else 0
    ok = (
        len(image_ids) == expected and
        '<!-- yo:auto-media:start -->' not in content and
        not bad_meta and
        all(' />' in b for _, b in image_blocks) and
        (expected == 0 or unique_headings >= min(expected, len(heading_events)))
    )
    print(json.dumps({
        'post_id': pid,
        'ok': ok,
        'expected_images': expected,
        'images': len(image_ids),
        'headings': len(heading_events),
        'unique_image_headings': unique_headings,
        'auto_region': '<!-- yo:auto-media:start -->' in content,
        'bad_meta': bad_meta,
        'placements': placements[:4],
        'meta_samples': meta_samples[:2],
    }, ensure_ascii=False))
