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

# Başlıkta bu kelimeler varsa reddet
_BLOCKED_TITLE_FRAGMENTS = (
    "hotel", "resort", "spa ", "waterpark", "water park",
    "bikini", "young woman", "woman smiling", "man smiling",
    "tourists posing", "couple", "selfie",
    "logo", "icon", "illustration", "vector", "clipart",
    "map of", "infographic", "banner", "poster", "flyer",
    "3d render", "3d model", "rendering",
)

# Minimum kalite eşiği
_MIN_WIDTH = 3000      # piksel — küçük stok fotoğrafları elenir
_MIN_DOWNLOADS = 2     # neredeyse hiç indirilmemiş = düşük kalite sinyali
_MIN_SCORE = 2         # toplam puan eşiği


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
    user = os.getenv("DEPOSIT_LOGIN_USER", "your_username")
    pwd = os.getenv("DEPOSIT_LOGIN_PASSWORD", "")
    r = _post({"dp_command": "login", "dp_apikey": api_key,
               "dp_login_user": user, "dp_login_password": pwd})
    if r.get("type") != "success":
        raise RuntimeError(f"DepositPhotos login başarısız: {r.get('error', {}).get('errormsg', r)}")
    return str(r["sessionid"])


def _score(result: Dict, query_words: list[str]) -> int:
    """Fotoğrafı puanla. Yüksek = daha iyi. Negatif = elenir."""
    title = (result.get("title") or "").lower()
    tags = " ".join(result.get("tags") or []).lower()

    # Hard reddetler
    if any(frag in title for frag in _BLOCKED_TITLE_FRAGMENTS):
        return -99
    if result.get("isIllustration") or result.get("nudity"):
        return -99
    width = int(result.get("width") or 0)
    if width < _MIN_WIDTH:
        return -99
    downloads = int(result.get("downloads") or 0)
    if downloads < _MIN_DOWNLOADS:
        return -1  # düşük ama tamamen reddetme

    score = 0

    # Boyut bonusu
    if width >= 5000:
        score += 2
    elif width >= 4000:
        score += 1

    # Popülerlik
    if downloads >= 100:
        score += 2
    elif downloads >= 30:
        score += 1

    # Query kelimeleri başlık/tag'de geçiyor mu
    for word in query_words:
        if len(word) >= 4:
            if word in title:
                score += 2
            elif word in tags:
                score += 1

    # Editorial fotoğraflar genelde daha otantik
    if result.get("iseditorial") or result.get("is_editorial"):
        score += 1

    return score


def _is_usable(result: Dict) -> bool:
    title = (result.get("title") or "").lower()
    return not any(frag in title for frag in _BLOCKED_TITLE_FRAGMENTS)


def search(query: str, count: int = 8, orientation: str = "horizontal") -> List[Dict[str, Any]]:
    """DepositPhotos'ta arama yapar, puanlar ve sıralar.

    Her sonuç: {id, title, score, preview_url, width, downloads}
    Sadece _MIN_SCORE üzerindeki fotoğraflar döner.
    """
    api_key = _api_key()
    # Fazla çek — filtreleme sonrası count kadar kalsın
    fetch_limit = max(count * 4, 20)
    r = _post({
        "dp_command": "search",
        "dp_apikey": api_key,
        "dp_search_query": query,
        "dp_search_limit": fetch_limit,
        "dp_search_offset": 0,
        "dp_search_orientation": orientation,
        "dp_search_nudity": 0,
    })
    if r.get("type") != "success":
        raise RuntimeError(f"DepositPhotos arama hatası: {r.get('error', {}).get('errormsg', r)}")

    results = r.get("result", [])
    if isinstance(results, dict):
        results = list(results.values())

    query_words = query.lower().split()

    # Puanla ve filtrele
    scored = []
    for v in results:
        s = _score(v, query_words)
        if s >= _MIN_SCORE:
            scored.append((s, v))

    # Skora göre sırala
    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        {
            "id": str(v["id"]),
            "title": v.get("title", ""),
            "score": s,
            "width": int(v.get("width") or 0),
            "downloads": int(v.get("downloads") or 0),
            "preview_url": v.get("url_big") or v.get("thumb_huge") or v.get("thumb380") or "",
        }
        for s, v in scored[:count]
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
