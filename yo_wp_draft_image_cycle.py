#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image

from settings import get_vil_dir, load_project_env
from visual_memory import VisualMemoryComponent, VisualMemoryConfig
from visual_memory.deposit_config import load_deposit_config
from run_deposit import api_key_for_download, download_url, infer_extension, licensed_download_link, login_password_for_download, login_session_id, login_user_for_download

ROOT = Path(__file__).resolve().parent
WP_PATH = Path('/home/yoldaolmak/public_html')
VIL_DIR = get_vil_dir()
LOG_DIR = ROOT / 'ops_logs' / 'draft_image_cycles'
BACKUP_DIR = ROOT / 'ops_backups' / 'draft_image_cycles'

STOPWORDS = {
    'nedir','nasil','nasıl','hangi','rehberi','basvuru','başvuru','icin','için','olan','olur',
    've','ile','bir','the','and','or','h2','adim','adım','kategori','pillar','prompt','daha',
    'once','önce','hic','hiç','bilmediginiz','bilmediğiniz','tuyolar','tüyolar'
}
PEOPLE_TERMS = {
    'people','person','man','woman','male','female','girl','boy','child','children',
    'traveler','traveller','tourist','portrait','face','smiling','holding','hand','hands',
    'couple','family','businessman','businesswoman','office','corporate','meeting','tie'
}

TR_TO_EN = {
    'vize': 'visa application travel documents embassy passport',
    'e-vize': 'online visa application passport airport immigration',
    'kapida': 'airport visa on arrival passport immigration counter',
    'kapıda': 'airport visa on arrival passport immigration counter',
    'dijital': 'digital nomad remote work laptop travel passport',
    'gocebe': 'digital nomad remote work laptop travel passport',
    'göçebe': 'digital nomad remote work laptop travel passport',
    'evrak': 'travel documents passport application forms folder',
    'evraklari': 'travel documents passport application forms folder',
    'evrakları': 'travel documents passport application forms folder',
    'reddi': 'visa refusal letter passport documents',
    'itiraz': 'appeal letter application documents passport',
    'pasaport': 'passport immigration border control travel documents',
    'sinir': 'border control passport immigration officer airport',
    'sınır': 'border control passport immigration officer airport',
    'telefon': 'smartphone travel esim airport mobile internet',
    'internet': 'smartphone travel esim mobile internet',
    'esim': 'smartphone esim travel mobile data',
    'gezi': 'travel planning map itinerary passport luggage',
    'plani': 'travel planning map itinerary laptop',
    'planı': 'travel planning map itinerary laptop',
    'hazirlik': 'travel preparation packing checklist passport luggage',
    'hazırlık': 'travel preparation packing checklist passport luggage',
    'evi': 'home closing checklist travel preparation suitcase',
    'kapatma': 'home preparation travel checklist suitcase',
    'ankara': 'ankara turkey landmarks museum lake nature travel',
    'cevresinde': 'day trips near ankara nature lake historic town',
    'çevresinde': 'day trips near ankara nature lake historic town',
    'gezilecek': 'travel destinations landmarks nature museum',
    'yerler': 'travel destinations landmarks nature museum',
    'kurtulus': 'turkey history museum architecture',
    'kurtuluş': 'turkey history museum architecture',
    'muzesi': 'museum historic building architecture',
    'müzesi': 'museum historic building architecture',
    'gol': 'lake nature landscape travel',
    'göl': 'lake nature landscape travel',
}


def run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(cmd, cwd=str(cwd or ROOT), env=merged_env, text=True, capture_output=True, check=check)


def wp(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return run(['wp', *args, '--allow-root'], cwd=WP_PATH, check=check)


def strip_html(value: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html.unescape(value or ''))).strip()


def post_json(post_id: int) -> dict:
    out = wp(['post', 'get', str(post_id), '--format=json']).stdout
    return json.loads(out)


def content_headings(content: str) -> list[str]:
    headings = []
    for match in re.finditer(r'<h[23][^>]*>(.*?)</h[23]>', content, flags=re.I | re.S):
        text = strip_html(match.group(1))
        if text:
            headings.append(text)
    for match in re.finditer(r'<!-- wp:heading.*?-->(.*?)<!-- /wp:heading -->', content, flags=re.I | re.S):
        text = strip_html(match.group(1))
        if text and text not in headings:
            headings.append(text)
    return headings[:8]


def tokens(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü0-9-]+", html.unescape(text or '').lower())
    clean = []
    for token in raw:
        token = token.strip('-')
        if len(token) < 3 or token in STOPWORDS:
            continue
        clean.append(token)
    return clean


def ascii_text(value: str) -> str:
    for src, dst in [
        ("ı", "i"), ("İ", "i"), ("ğ", "g"), ("Ğ", "g"), ("ü", "u"), ("Ü", "u"),
        ("ş", "s"), ("Ş", "s"), ("ö", "o"), ("Ö", "o"), ("ç", "c"), ("Ç", "c"),
    ]:
        value = value.replace(src, dst)
    return value.lower()


def topic_base(title: str, headings: list[str]) -> str:
    text = ascii_text(title + " " + " ".join(headings[:3]))
    rules = [
        (("e-vize", "kapida"), "passport visa application airport immigration"),
        (("dijital", "gocebe"), "digital nomad remote work laptop passport"),
        (("evrak", "belge", "dosya"), "visa documents passport application form"),
        (("reddi", "itiraz", "red"), "visa refusal documents passport letter"),
        (("sinir", "pasaport kontrol"), "passport border control airport immigration"),
        (("telefon", "internet", "esim"), "travel esim smartphone airport"),
        (("gezi plan", "rota", "harita"), "travel planning map itinerary laptop"),
        (("evi", "kapatma"), "travel preparation home checklist suitcase"),
        (("hazirlik", "ekipman"), "travel packing checklist passport suitcase"),
        (("vize",), "passport visa application documents"),
    ]
    for needles, base in rules:
        if any(needle in text for needle in needles):
            return base
    source_tokens = tokens(title + " " + " ".join(headings[:2]))
    mapped = []
    for token in source_tokens[:6]:
        mapped.extend(TR_TO_EN.get(token, token).split()[:4])
    return " ".join(mapped[:8]) or "travel preparation passport suitcase"


def build_queries(title: str, headings: list[str], count: int) -> list[str]:
    base = topic_base(title, headings)
    templates = [
        "ankara turkey museum landmark",
        "ankara turkey nature lake",
        "ankara turkey travel landmark",
        f"{base} no people",
        base,
        f"{base} landmark museum nature",
        f"{base} friendly travel objects no people",
        f"{base} natural travel landscape no people",
        f"{base} planning checklist no people",
        "travel planning map passport luggage no people",
    ]
    deduped = []
    seen = set()
    for q in templates:
        q = ascii_text(re.sub(r"\s+", " ", q).strip())
        key = q.lower()
        if key not in seen:
            deduped.append(q[:90])
            seen.add(key)
    return deduped[:max(count + 2, 6)]

def component() -> VisualMemoryComponent:
    settings = load_deposit_config(ROOT / 'depositphotos_credentials.json')
    return VisualMemoryComponent(VisualMemoryConfig(
        database_path=ROOT / 'data' / 'visual_memory.db',
        depositphotos_search_url=settings.get('search_url'),
        depositphotos_api_key=settings.get('api_key'),
        depositphotos_api_secret=settings.get('api_secret'),
        depositphotos_affiliate_id=settings.get('affiliate_id') or settings.get('account'),
    ))


def download_licensed_asset(asset_id: str, dest: Path, settings: dict[str, str], session_cache: dict[str, str]) -> Path:
    api_key = api_key_for_download(settings)
    if 'session_id' not in session_cache:
        session_cache['session_id'] = login_session_id(
            api_key,
            login_user_for_download(settings),
            login_password_for_download(settings),
        )
    media_url = licensed_download_link(api_key, session_cache['session_id'], str(asset_id))
    tmp = dest.with_suffix(infer_extension(media_url))
    download_url(media_url, tmp)
    with Image.open(tmp) as img:
        img.convert('RGB').save(dest, format='JPEG', quality=94)
    tmp.unlink(missing_ok=True)
    return dest


def backup_post(post: dict, cycle_id: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    path = BACKUP_DIR / f'{cycle_id}-post-{post["ID"]}.json'
    path.write_text(json.dumps(post, ensure_ascii=False, indent=2))
    return path


def clear_cycle_vil() -> None:
    VIL_DIR.mkdir(parents=True, exist_ok=True)
    for path in list(VIL_DIR.glob('yo-cycle-*')) + list(VIL_DIR.glob('yo-licensed-*')):
        if path.is_file():
            path.unlink()


def find_candidates(comp: VisualMemoryComponent, queries: list[str], needed: int) -> list[dict]:
    chosen = []
    seen = set()
    for query in queries:
        try:
            results = comp.search_depositphotos(query, limit=12, page=1)
        except Exception as exc:
            chosen.append({'error': f'{query}: {exc}'})
            continue
        for item in results:
            if not item.preview_url or not item.asset_id or item.asset_id in seen:
                continue
            title_text = ascii_text(item.title or "")
            title_terms = set(re.findall(r"[a-z0-9]+", title_text))
            if title_terms & PEOPLE_TERMS:
                continue
            seen.add(item.asset_id)
            chosen.append({
                'asset_id': item.asset_id,
                'title': item.title,
                'preview_url': item.preview_url,
                'landing_url': item.landing_url,
                'query': query,
                'width': item.width,
                'height': item.height,
            })
            if len([c for c in chosen if 'preview_url' in c]) >= needed:
                return [c for c in chosen if 'preview_url' in c]
    return [c for c in chosen if 'preview_url' in c]


def run_yo_upload(post_id: int, count: int) -> dict:
    env = {
        'YO_ENABLE_PAID_VISION': '0',
        'YO_ENABLE_PAID_DEPOSITPHOTOS': '0',
        'YO_ALLOW_FALLBACK_UPLOAD': '1',
        'YO_VIL_DIR': str(VIL_DIR),
        'OPENAI_API_KEY': '',
        'OPENAI_API_KEY_2': '',
        'OPENAI_API_KEY_3': '',
        'OPENAI_API_KEY_4': '',
        'ANTHROPIC_API_KEY': '',
    }
    proc = run(['./yo_cli.sh', f'{count} foto yo {post_id}'], cwd=ROOT, env=env, check=False)
    return {'returncode': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}


def verify_post(post_id: int, before_images: int) -> dict:
    post = post_json(post_id)
    content = post.get('post_content') or ''
    image_ids = [int(x) for x in re.findall(r'wp-image-(\d+)', content)]
    unique_ids = list(dict.fromkeys(image_ids))
    attachment_checks = []
    for mid in unique_ids[-8:]:
        meta_alt = wp(['post', 'meta', 'get', str(mid), '_wp_attachment_image_alt'], check=False).stdout.strip()
        att = wp(['post', 'get', str(mid), '--format=json'], check=False)
        title = caption = status = ''
        if att.returncode == 0 and att.stdout.strip():
            try:
                data = json.loads(att.stdout)
                title = data.get('post_title') or ''
                caption = data.get('post_excerpt') or ''
                status = data.get('post_status') or ''
            except Exception:
                pass
        attachment_checks.append({'id': mid, 'alt_ok': bool(meta_alt), 'title_ok': bool(title), 'caption_ok': bool(caption), 'status': status})
    return {
        'image_count_before': before_images,
        'image_count_after': len(unique_ids),
        'inserted_delta': max(0, len(unique_ids) - before_images),
        'auto_region': '<!-- yo:auto-media:start -->' in content,
        'attachments': attachment_checks,
        'meta_all_ok': all(a['alt_ok'] and a['title_ok'] and a['caption_ok'] for a in attachment_checks[-5:]) if attachment_checks else False,
    }


def list_targets() -> list[int]:
    vize = json.loads(wp(['post', 'list', '--post_type=post', '--post_status=draft', '--category_name=vize', '--fields=ID', '--format=json']).stdout)
    haz = json.loads(wp(['post', 'list', '--post_type=post', '--post_status=draft', '--tag=hazirlik', '--fields=ID', '--format=json']).stdout)
    ids = [int(x['ID']) for x in vize] + [int(x['ID']) for x in haz]
    deduped = []
    for pid in ids:
        if pid not in deduped:
            deduped.append(pid)
    return deduped


def process_post(post_id: int, comp: VisualMemoryComponent, count: int, cycle: int, cycle_id: str) -> dict:
    post = post_json(post_id)
    title = html.unescape(post.get('post_title') or '')
    content = post.get('post_content') or ''
    headings = content_headings(content)
    before_images = len(set(re.findall(r'wp-image-(\d+)', content)))
    if before_images >= count:
        return {'post_id': post_id, 'title': title, 'skipped': 'already_has_target_images', 'images': before_images}
    backup = backup_post(post, cycle_id)
    if len(strip_html(content)) < 1800 or 'prompt' in title.lower():
        return {'post_id': post_id, 'title': title, 'skipped': 'empty_or_prompt', 'content_chars': len(strip_html(content))}
    if len(headings) < 2:
        return {'post_id': post_id, 'title': title, 'skipped': 'no_hierarchical_headings', 'content_chars': len(strip_html(content)), 'headings': headings}
    queries = build_queries(title, headings, count)
    clear_cycle_vil()
    candidates = find_candidates(comp, queries, count)
    downloaded = []
    errors = []
    settings = load_deposit_config(ROOT / 'depositphotos_credentials.json')
    session_cache: dict[str, str] = {}
    for i, cand in enumerate(candidates[:count], 1):
        slug = re.sub(r'[^a-z0-9]+', '-', (title.lower() + '-' + str(cand['asset_id']))).strip('-')[:90]
        dest = VIL_DIR / f'yo-licensed-{cycle:02d}-{post_id}-{i}-{slug}.jpg'
        try:
            download_licensed_asset(str(cand['asset_id']), dest, settings, session_cache)
            downloaded.append(str(dest))
        except Exception as exc:
            errors.append({'asset_id': cand.get('asset_id'), 'error': str(exc), 'mode': 'licensed'})
    if len(downloaded) < max(2, count // 2):
        return {'post_id': post_id, 'title': title, 'backup': str(backup), 'queries': queries, 'downloaded': downloaded, 'errors': errors, 'status': 'failed_download_threshold'}
    upload = run_yo_upload(post_id, min(count, len(downloaded)))
    verify = verify_post(post_id, before_images)
    return {
        'post_id': post_id,
        'title': title,
        'content_chars': len(strip_html(content)),
        'headings': headings[:5],
        'backup': str(backup),
        'queries': queries,
        'candidates': candidates[:count],
        'downloaded': downloaded,
        'download_errors': errors,
        'upload': upload,
        'verify': verify,
        'status': 'success' if upload['returncode'] == 0 and verify['inserted_delta'] >= min(count, len(downloaded)) and verify['meta_all_ok'] else 'needs_review',
    }


def main() -> None:
    load_project_env()
    parser = argparse.ArgumentParser()
    parser.add_argument('--cycles', type=int, default=5)
    parser.add_argument('--count', type=int, default=4)
    parser.add_argument('--sleep', type=float, default=0.0)
    args = parser.parse_args()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    cycle_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = LOG_DIR / f'{cycle_id}.jsonl'
    comp = component()
    targets = list_targets()
    processed = 0
    with log_path.open('a') as log:
        for post_id in targets:
            if processed >= args.cycles:
                break
            result = process_post(post_id, comp, args.count, processed + 1, cycle_id)
            result['cycle'] = processed + 1
            result['ts'] = datetime.now().isoformat(timespec='seconds')
            log.write(json.dumps(result, ensure_ascii=False) + '\n')
            log.flush()
            print(json.dumps({k: result.get(k) for k in ['cycle','post_id','title','status','verify']}, ensure_ascii=False))
            processed += 1
            if args.sleep:
                time.sleep(args.sleep)
    print(f'log={log_path}')

if __name__ == '__main__':
    main()
