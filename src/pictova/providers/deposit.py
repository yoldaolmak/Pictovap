"""DepositPhotos provider — arama + lisanslı indirme."""

from __future__ import annotations

import json
import os
import ssl
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


_API_URL = "https://api.depositphotos.com/"

# Türkçe içerik için alakasız filtreler
_BLOCKED_TITLE_FRAGMENTS = (
    "hotel", "resort", "spa ", "waterpark", "bikini",
    "young woman", "woman smiling", "man smiling", "tourists posing",
    "logo", "icon", "illustration", "vector", "clipart",
)


def _ssl_ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _post(payload: Dict) -> Dict:
    req = urllib.request.Request(
        _API_URL,
        data=urllib.parse.urlencode(payload).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30, context=_ssl_ctx()) as r:
        return json.loads(r.read())


def _api_key() -> str:
    key = os.getenv("DEPOSIT_API_KEY", "")
    if not key:
        raise RuntimeError("DEPOSIT_API_KEY bulunamadı — .env dosyasını kontrol et")
    return key


def _login() -> str:
    """Session ID döner (her çağrıda yeni session açar)."""
    api_key = _api_key()
    user = os.getenv("DEPOSIT_LOGIN_USER", "yoldaolmak")
    pwd = os.getenv("DEPOSIT_LOGIN_PASSWORD", "")
    r = _post({"dp_command": "login", "dp_apikey": api_key,
                "dp_login_user": user, "dp_login_password": pwd})
    if r.get("type") != "success":
        raise RuntimeError(f"DepositPhotos login başarısız: {r.get('error', {}).get('errormsg', r)}")
    return str(r["sessionid"])


def _is_usable(result: Dict) -> bool:
    title = (result.get("title") or "").lower()
    return not any(frag in title for frag in _BLOCKED_TITLE_FRAGMENTS)


def search(query: str, count: int = 8, orientation: str = "horizontal") -> List[Dict[str, Any]]:
    """DepositPhotos'ta arama yapar. Her sonuç: {id, title, preview_url}."""
    api_key = _api_key()
    r = _post({
        "dp_command": "search",
        "dp_apikey": api_key,
        "dp_search_query": query,
        "dp_search_limit": count * 2,  # filtreleme için fazla çek
        "dp_search_offset": 0,
        "dp_search_orientation": orientation,
        "dp_search_nudity": 0,
    })
    if r.get("type") != "success":
        raise RuntimeError(f"DepositPhotos arama hatası: {r.get('error', {}).get('errormsg', r)}")

    results = r.get("result", [])
    if isinstance(results, dict):
        results = list(results.values())

    filtered = [v for v in results if _is_usable(v)]
    return [
        {
            "id": str(v["id"]),
            "title": v.get("title", ""),
            "preview_url": v.get("thumb380") or v.get("thumb_big") or v.get("url_big") or "",
        }
        for v in filtered[:count]
    ]


def download(asset_id: str, session_id: str, dest_dir: Optional[str] = None) -> str:
    """Lisanslı XL dosyayı indir, yerel path döner."""
    api_key = _api_key()
    r = _post({
        "dp_command": "getMedia",
        "dp_apikey": api_key,
        "dp_session_id": session_id,
        "dp_media_id": asset_id,
        "dp_media_option": "xl",
        "dp_media_license": "standard",
    })
    if r.get("type") != "success":
        err = r.get("error", {})
        raise RuntimeError(f"DepositPhotos indirme hatası ({asset_id}): {err.get('errormsg', err)}")

    dl_url = r["downloadLink"]
    out_dir = Path(dest_dir) if dest_dir else Path(tempfile.mkdtemp(prefix="pictova_dep_"))
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"deposit_{asset_id}.jpg"

    req = urllib.request.Request(dl_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60, context=_ssl_ctx()) as resp:
        dest.write_bytes(resp.read())

    return str(dest)


def search_and_download(
    query: str,
    count: int = 4,
    dest_dir: Optional[str] = None,
    orientation: str = "horizontal",
) -> List[str]:
    """Arama + indirme birleşik. Yerel dosya path listesi döner."""
    session_id = _login()
    results = search(query, count=count, orientation=orientation)
    if not results:
        raise RuntimeError(f"DepositPhotos'ta sonuç bulunamadı: {query!r}")

    paths = []
    for r in results[:count]:
        try:
            path = download(r["id"], session_id, dest_dir=dest_dir)
            paths.append(path)
        except RuntimeError as e:
            print(f"  ⚠ Atlandı ({r['id']}): {e}")
    return paths


__all__ = ["search", "download", "search_and_download", "_login"]
