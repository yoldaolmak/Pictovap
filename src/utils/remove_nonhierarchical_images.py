#!/usr/bin/env python3
import json
import re
from datetime import datetime
from pathlib import Path
from src.core.yo_wp_uploader import YOWordPressUploader

ids = [249223, 264454, 152168]
u = YOWordPressUploader(site='yoldaolmak')
backup_dir = Path('/YOOS-VIL/ops_backups/remove_nonhierarchical_images')
backup_dir.mkdir(parents=True, exist_ok=True)
for pid in ids:
    post = u.fetch_post_context(pid)
    content = post.get('content_raw', '') or ''
    backup = backup_dir / (datetime.now().strftime('%Y%m%d_%H%M%S') + '-post-' + str(pid) + '.html')
    backup.write_text(content)
    removed = len(set(re.findall(r'wp-image-(\d+)', content)))
    new = re.sub(r'<!-- wp:image\b.*?<!-- /wp:image -->\s*', '', content, flags=re.S | re.I).strip() + '\n'
    resp = u.session.post(u.base_url + '/wp-json/wp/v2/posts/' + str(pid), json={'content': new}, timeout=60)
    print(json.dumps({'post_id': pid, 'removed': removed, 'status': resp.status_code, 'backup': str(backup)}, ensure_ascii=False))
