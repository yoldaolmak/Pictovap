#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests

from yo_image_processor import YOImageProcessor
from yo_gutenberg_blocks import native_gallery_block

POST_ID = 265143
WP_PATH = Path('/home/yoldaolmak/public_html')
ROOT = Path('/home/ai/YOOS-VIL')
WORK = Path('/tmp/yo_savsat_commons')
LOCAL_SOURCES = Path('/tmp/savsat_commons_sources')
BACKUP_DIR = ROOT / 'ops_backups' / 'savsat_commons_265143'
COMMONS_API = 'https://commons.wikimedia.org/w/api.php'
USER_AGENT = 'YOOS-VIL/1.0 (yoldaolmak image workflow)'

ITEMS = [
    {
        'title': 'File:Şavşat1.JPG',
        'slug': 'savsat-yesil-vadi-manzarasi',
        'heading': 'Ne zaman gidilir?',
        'wp_title': 'Şavşat yeşil vadi manzarası',
        'alt': 'Şavşat gezi rehberi için yeşil vadi ve dağ manzarası',
        'caption': 'Şavşat, yılın en güçlü etkisini yeşilin yoğun olduğu geç bahar ve yaz aylarında gösterir.',
        'description': 'Şavşat mevsim seçimi ve doğa atmosferini anlatan lisanslı Wikimedia Commons görseli.',
    },
    {
        'title': 'File:Şavşat - panoramio.jpg',
        'slug': 'savsat-koy-ve-dag-dokusu',
        'heading': 'Ne zaman gidilir?',
        'wp_title': 'Şavşat köy ve dağ dokusu',
        'alt': 'Şavşat köyleri ve çevresindeki dağlık doğa dokusu',
        'caption': 'Şavşat rotasında hava ve mevsim, manzarayı doğrudan değiştiren ana unsur.',
        'description': 'Şavşat köyleri, yayla havası ve mevsim planlaması için lisanslı Wikimedia Commons görseli.',
    },
    {
        'title': 'File:Artvin Şavşat Karagöl.jpg',
        'slug': 'savsat-karagol-gol-manzarasi',
        'heading': 'Karagöl ve Sahara — ana duraklar',
        'wp_title': 'Şavşat Karagöl göl manzarası',
        'alt': 'Şavşat Karagöl kıyısında ormanla çevrili göl manzarası',
        'caption': 'Karagöl, Şavşat rotasının en sakin ve en güçlü doğa duraklarından biri.',
        'description': 'Şavşat Karagöl bölümünü destekleyen lisanslı Wikimedia Commons görseli.',
    },
    {
        'title': 'File:Artvin Şavşat Karagöl, yansımalar.jpg',
        'slug': 'savsat-karagol-yansimalar',
        'heading': 'Karagöl ve Sahara — ana duraklar',
        'wp_title': 'Şavşat Karagöl yansımaları',
        'alt': 'Şavşat Karagöl üzerinde orman ve dağ yansımaları',
        'caption': 'Karagöl çevresinde kısa yürüyüşler, göl manzarasını farklı açılardan görmeyi sağlar.',
        'description': 'Karagöl ve Sahara Milli Parkı anlatımı için lisanslı Wikimedia Commons görseli.',
    },
    {
        'title': 'File:Karagöl-Sahara National Park- 2019.jpg',
        'slug': 'karagol-sahara-milli-parki',
        'heading': 'Rota önerileri',
        'wp_title': 'Karagöl Sahara Milli Parkı rotası',
        'alt': 'Karagöl Sahara Milli Parkı içinde orman ve doğa rotası',
        'caption': 'Rota planında Karagöl ve Sahara’yı aynı güne sıkıştırmak mümkün, ama acele etmemek daha iyi sonuç verir.',
        'description': 'Şavşat rota önerileri ve Karagöl Sahara Milli Parkı bölümü için lisanslı Wikimedia Commons görseli.',
    },
    {
        'title': "File:Artvin Şavşat Karagöl'den Kaçkar dağları.jpg",
        'slug': 'savsat-karagolden-kackar-daglari',
        'heading': 'Rota önerileri',
        'wp_title': 'Şavşat Karagöl’den Kaçkar dağları',
        'alt': 'Şavşat Karagöl çevresinden görülen Kaçkar Dağları manzarası',
        'caption': 'Şavşat’ta iyi rota, sadece durakları değil manzaralar arasındaki geçişleri de hesaba katar.',
        'description': 'Şavşat rota önerilerini ve doğa geçişlerini anlatan lisanslı Wikimedia Commons görseli.',
    },
    {
        'title': 'File:Şavşat Evleri - Artvin.jpg',
        'slug': 'savsat-evleri-artvin',
        'heading': 'Yeme içme, konaklama ve pratik bilgiler',
        'wp_title': 'Şavşat evleri ve yerel doku',
        'alt': 'Artvin Şavşat evleri ve yerel kırsal mimari dokusu',
        'caption': 'Konaklama seçerken Şavşat’ın dağınık köy dokusunu ve yol sürelerini hesaba katmak gerekir.',
        'description': 'Şavşat konaklama ve yerel doku bilgilerini destekleyen lisanslı Wikimedia Commons görseli.',
    },
    {
        'title': 'File:08790 Pınarlı-Şavşat-Artvin, Turkey - panoramio.jpg',
        'slug': 'pinarli-savsat-artvin-doga',
        'heading': 'Yeme içme, konaklama ve pratik bilgiler',
        'wp_title': 'Pınarlı Şavşat Artvin doğası',
        'alt': 'Pınarlı Şavşat Artvin çevresinde doğal kırsal manzara',
        'caption': 'Şavşat’ta pratik plan, doğa kadar köyler arası mesafeyi ve sakin tempoyu da önemser.',
        'description': 'Şavşat pratik gezi planı ve kırsal çevre için lisanslı Wikimedia Commons görseli.',
    },
]


def wp(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(['wp', *args, '--allow-root'], cwd=str(WP_PATH), text=True, capture_output=True, check=check)


def post_content() -> str:
    return wp(['post', 'get', str(POST_ID), '--field=post_content']).stdout


def backup(content: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    path = BACKUP_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}-post-{POST_ID}.html"
    path.write_text(content)
    return path


def commons_info(title: str) -> dict:
    s = requests.Session()
    s.headers.update({'User-Agent': USER_AGENT})
    params = {
        'action': 'query',
        'titles': title,
        'prop': 'imageinfo',
        'iiprop': 'url|extmetadata|mime|size',
        'iiurlwidth': 2200,
        'format': 'json',
    }
    resp = s.get(COMMONS_API, params=params, timeout=30)
    resp.raise_for_status()
    pages = resp.json().get('query', {}).get('pages', {})
    page = next(iter(pages.values()))
    info = page['imageinfo'][0]
    meta = info.get('extmetadata', {})
    def mv(key: str) -> str:
        value = meta.get(key, {})
        return html.unescape(re.sub('<[^<]+?>', '', str(value.get('value', '')))).strip()
    return {
        'url': info.get('thumburl') or info['url'],
        'width': info.get('thumbwidth') or info.get('width'),
        'height': info.get('thumbheight') or info.get('height'),
        'license': mv('LicenseShortName'),
        'artist': mv('Artist'),
        'credit': mv('Credit'),
        'source': mv('ObjectName') or title.replace('File:', ''),
        'description_url': info.get('descriptionurl') or f"https://commons.wikimedia.org/wiki/{quote(title.replace(' ', '_'))}",
    }


def download(url: str, path: Path) -> Path:
    r = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=60)
    r.raise_for_status()
    path.write_bytes(r.content)
    return path


def gallery_block(items: list[dict]) -> str:
    return native_gallery_block(items, columns=2)


def normalize(value: str) -> str:
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', value))).strip().lower()


def insert_after_heading(content: str, heading: str, block: str) -> str:
    if normalize(heading) == 'nasıl gidilir?':
        raise RuntimeError('Refusing to insert under Nasıl gidilir')
    pattern = re.compile(r'(?:<!-- wp:heading(?:\s+\{.*?\})? -->\s*)?<h(?P<level>[23])\b[^>]*>.*?</h(?P=level)>\s*(?:<!-- /wp:heading -->)?', re.S | re.I)
    target = normalize(heading)
    for m in pattern.finditer(content):
        htext = normalize(m.group(0))
        if target in htext:
            before_next = content[m.end():]
            next_heading = pattern.search(before_next)
            section = before_next[:next_heading.start()] if next_heading else before_next
            if 'wp:image' in section or 'wp:gallery' in section:
                # Leave existing editorial image blocks intact; insert directly after heading only once.
                pass
            return content[:m.end()].rstrip() + '\n\n' + block + '\n\n' + content[m.end():].lstrip()
    raise RuntimeError(f'Heading not found: {heading}')


def media_url(media_id: int) -> str:
    code = f'echo wp_get_attachment_url({media_id});'
    return wp(['eval', code]).stdout.strip()


def upload_file(path: Path, item: dict, info: dict) -> dict:
    credit = f"Kaynak: Wikimedia Commons; lisans: {info['license']}; sanatçı/yükleyen: {info['artist'] or 'belirtilmemiş'}; dosya: {info['description_url']}"
    description = f"{item['description']} {credit}"
    imported = wp([
        'media', 'import', str(path),
        '--post_id=' + str(POST_ID),
        '--title=' + item['wp_title'],
        '--caption=' + item['caption'],
        '--desc=' + description,
        '--porcelain',
    ]).stdout.strip()
    media_id = int(imported.splitlines()[-1])
    wp(['post', 'meta', 'update', str(media_id), '_wp_attachment_image_alt', item['alt']])
    url = media_url(media_id)
    return {**item, **info, 'media_id': media_id, 'url': url, 'processed': str(path)}


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    original = post_content()
    backup_path = backup(original)
    processor = YOImageProcessor(work_dir=WORK)
    uploaded = []
    for idx, item in enumerate(ITEMS, 1):
        info = commons_info(item['title'])
        raw = WORK / f"{idx:02d}-{item['slug']}-source.jpg"
        out = WORK / f"{idx:02d}-{item['slug']}.webp"
        local_source = LOCAL_SOURCES / f"{idx:02d}-{item['slug']}.jpg"
        if local_source.exists():
            shutil.copyfile(local_source, raw)
        else:
            download(info['url'], raw)
        result = processor.process_image(str(raw), str(out), auto_saturation=True)
        if result.get('is_panoramic'):
            raise RuntimeError(f"Panoramic image rejected: {item['title']}")
        uploaded.append(upload_file(out, item, info))

    grouped = []
    for heading in ['Ne zaman gidilir?', 'Karagöl ve Sahara — ana duraklar', 'Rota önerileri', 'Yeme içme, konaklama ve pratik bilgiler']:
        group = [u for u in uploaded if u['heading'] == heading]
        grouped.append((heading, gallery_block(group)))

    content = original
    for heading, block in reversed(grouped):
        content = insert_after_heading(content, heading, block)
    wp(['post', 'update', str(POST_ID), '--post_content=' + content])

    log = {
        'post_id': POST_ID,
        'backup': str(backup_path),
        'uploaded': [{k: u[k] for k in ['media_id','title','heading','license','artist','url']} for u in uploaded],
        'headings_used': [h for h, _ in grouped],
        'forbidden_heading_used': 'Nasıl gidilir?' in ''.join([h for h, _ in grouped]),
    }
    log_path = ROOT / 'ops_logs' / f"savsat_265143_commons_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2))
    print(json.dumps(log, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
