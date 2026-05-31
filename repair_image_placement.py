#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

from yo_wp_uploader import YOWordPressUploader

WP_PATH = Path("/home/yoldaolmak/public_html")
ROOT = Path("/YOOS-VIL")
BACKUP_DIR = ROOT / "ops_backups" / "image_placement_repair"
LOG_DIR = ROOT / "ops_logs" / "image_placement_repair"
AUTO_RE = re.compile(r"<!-- yo:auto-media:start -->.*?<!-- yo:auto-media:end -->\s*", re.S)
IMG_BLOCK_RE = re.compile(r"<!-- wp:image\b.*?<!-- /wp:image -->\s*", re.S)
HEADING_RE = re.compile(
    r"(?:<!-- wp:heading(?:\s+\{.*?\})? -->\s*)?<h[23]\b[^>]*>.*?</h[23]>\s*(?:<!-- /wp:heading -->)?",
    re.S | re.I,
)


def wp(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["wp", *args, "--allow-root"], cwd=str(WP_PATH), text=True, capture_output=True, check=check)


def post_json(pid: int) -> dict:
    return json.loads(wp(["post", "get", str(pid), "--format=json"]).stdout)


def strip_tags(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(value or ""))).strip()


def media_record(mid: int, fallback_url: str = "", fallback_alt: str = "", fallback_caption: str = "") -> dict:
    alt = strip_tags(fallback_alt)[:160]
    title = alt or f"image-{mid}"
    caption = strip_tags(fallback_caption or title)[:220]
    return {"id": mid, "url": fallback_url or "", "alt": alt, "title": title, "caption": caption}

def canonical_block(media: dict) -> str:
    mid = int(media["id"])
    url = html.escape(str(media.get("url") or ""), quote=True)
    alt = html.escape(str(media.get("alt") or ""), quote=True)
    caption = html.escape(str(media.get("caption") or ""))
    block = (
        f'<!-- wp:image {{"id":{mid},"sizeSlug":"full","linkDestination":"none"}} -->\n'
        f'<figure class="wp-block-image size-full"><img src="{url}" alt="{alt}" class="wp-image-{mid}" />'
    )
    if caption:
        block += f'<figcaption class="wp-element-caption">{caption}</figcaption>'
    block += "</figure>\n<!-- /wp:image -->"
    return block


def extract_media_from_auto(content: str) -> list[dict]:
    match = AUTO_RE.search(content)
    blocks = IMG_BLOCK_RE.findall(match.group(0) if match else content)
    media = []
    seen = set()
    for block in blocks:
        id_match = re.search(r'"id"\s*:\s*(\d+)', block) or re.search(r"wp-image-(\d+)", block)
        if not id_match:
            continue
        mid = int(id_match.group(1))
        if mid in seen:
            continue
        seen.add(mid)
        src = re.search(r'<img[^>]+src="([^"]+)"', block)
        alt = re.search(r'<img[^>]+alt="([^"]*)"', block)
        cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", block, re.S)
        media.append(
            media_record(
                mid,
                src.group(1) if src else "",
                html.unescape(alt.group(1)) if alt else "",
                strip_tags(cap.group(1)) if cap else "",
            )
        )
    return media


def remove_existing_image_ids(content: str, media_ids: list[int]) -> str:
    result = content
    for mid in media_ids:
        result = re.sub(
            rf"<!-- wp:image\b(?:(?!<!-- /wp:image -->).)*wp-image-{mid}.*?<!-- /wp:image -->\s*",
            "",
            result,
            flags=re.S,
        )
    return result


def insert_balanced(content: str, blocks: list[str], media_ids: list[int]) -> str:
    clean = AUTO_RE.sub("", content)
    clean = remove_existing_image_ids(clean, media_ids).strip() + "\n"
    headings = list(HEADING_RE.finditer(clean))
    if not headings:
        return clean.rstrip() + "\n\n" + "\n\n".join(blocks) + "\n"
    result = clean
    offset = 0
    for idx, block in enumerate(blocks):
        heading = headings[min(idx, len(headings) - 1)]
        insert_at = heading.end() + offset
        addition = "\n\n" + block + "\n\n"
        result = result[:insert_at].rstrip() + addition + result[insert_at:].lstrip()
        offset += len(addition)
    return result.strip() + "\n"


def repair(pid: int) -> dict:
    post = post_json(pid)
    content = post.get("post_content") or ""
    media = extract_media_from_auto(content)
    if not media:
        return {"post_id": pid, "status": "skipped", "reason": "no images"}
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}-post-{pid}.json"
    backup.write_text(json.dumps(post, ensure_ascii=False, indent=2))
    blocks = [canonical_block(m) for m in media]
    new_content = insert_balanced(content, blocks, [int(m["id"]) for m in media])
    uploader = YOWordPressUploader(site="yoldaolmak")
    endpoint = f"{uploader.base_url}/wp-json/wp/v2/posts/{pid}"
    wp_stderr = ""
    update_ok = False
    try:
        response = uploader.session.post(endpoint, json={"content": new_content}, timeout=60)
        update_ok = response.status_code < 400
        if not update_ok:
            wp_stderr = response.text[-500:]
    except Exception as exc:
        wp_stderr = str(exc)[-500:]
    after = new_content if update_ok else content
    image_ids = list(dict.fromkeys(re.findall(r"wp-image-(\d+)", after)))
    return {
        "post_id": pid,
        "status": "updated" if update_ok else "failed",
        "images": len(image_ids),
        "auto_region": "<!-- yo:auto-media:start -->" in after,
        "backup": str(backup),
        "wp_stderr": wp_stderr,
        "headings_seen": len(list(HEADING_RE.finditer(after))),
    }


def main() -> None:
    ids = [264462, 264463, 264486, 264459, 264458, 264585, 249223, 264454, 264532, 264525, 264528, 152168]
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    with log_path.open("a") as log:
        for pid in ids:
            result = repair(pid)
            log.write(json.dumps(result, ensure_ascii=False) + "\n")
            print(json.dumps(result, ensure_ascii=False))
    print(f"log={log_path}")


if __name__ == "__main__":
    main()
