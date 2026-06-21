#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from scripts.run_deposit import (
    api_key_for_download,
    download_url,
    infer_extension,
    licensed_download_link,
    login_password_for_download,
    login_session_id,
    login_user_for_download,
)
from src.core.settings import get_vil_dir, load_project_env
from src.visual_memory.deposit_config import load_deposit_config

load_project_env()
ASSETS = [
    ("200766508", "airport-security-personal-belongings-tray"),
    ("200766616", "airport-security-luggage-conveyor"),
]
ROOT = Path('/YOOS-VIL')
VIL = get_vil_dir()
TMP = ROOT / 'tmp' / 'licensed_deposit'


def main() -> None:
    settings = load_deposit_config(ROOT / 'depositphotos_credentials.json')
    api_key = api_key_for_download(settings)
    user = login_user_for_download(settings)
    password = login_password_for_download(settings)
    session_id = login_session_id(api_key, user, password)
    VIL.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    for old in VIL.glob('yo-licensed-*'):
        if old.is_file():
            old.unlink()
    results = []
    for idx, (asset_id, slug) in enumerate(ASSETS, 1):
        media_url = licensed_download_link(api_key, session_id, asset_id)
        ext = infer_extension(media_url)
        raw_path = TMP / f'{asset_id}{ext}'
        download_url(media_url, raw_path)
        final_path = VIL / f'yo-licensed-264443-{idx}-{slug}.jpg'
        with Image.open(raw_path) as img:
            img.convert('RGB').save(final_path, format='JPEG', quality=94)
        results.append({
            'asset_id': asset_id,
            'file': str(final_path),
            'bytes': final_path.stat().st_size,
            'raw_bytes': raw_path.stat().st_size,
            'mode': 'licensed',
        })
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
