"""DepositPhotos image source adapter — search + licensed download."""

from __future__ import annotations

import json
import os
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


_API_URL = "https://api.depositphotos.com/"

# Reject any result whose title contains one of these fragments.
_BLOCKED_TITLE_FRAGMENTS = (
    "hotel", "resort", "spa ", "waterpark", "water park",
    "bikini", "young woman", "woman smiling", "man smiling",
    "tourists posing", "couple", "selfie",
    "logo", "icon", "illustration", "vector", "clipart",
    "map of", "infographic", "banner", "poster", "flyer",
    "3d render", "3d model", "rendering",
)

# Minimum quality thresholds.
_MIN_WIDTH = 3000      # pixels — filters out small/low-res stock photos
_MIN_DOWNLOADS = 2     # near-zero downloads is a low-quality signal
_MIN_SCORE = 2         # total score threshold


def _post(payload: Dict) -> Dict:
    req = urllib.request.Request(
        _API_URL,
        data=urllib.parse.urlencode(payload).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    # Uses the default SSL context (full certificate + hostname verification).
    # This endpoint carries the account login/API key, so it must never be
    # sent over an unverified connection.
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _api_key() -> str:
    key = os.getenv("DEPOSIT_API_KEY", "")
    if not key:
        raise RuntimeError("DEPOSIT_API_KEY not found — check your .env file")
    return key


def _login() -> str:
    """Return a session ID (opens a new session on every call)."""
    api_key = _api_key()
    user = os.getenv("DEPOSIT_LOGIN_USER", "your_username")
    pwd = os.getenv("DEPOSIT_LOGIN_PASSWORD", "")
    r = _post({"dp_command": "login", "dp_apikey": api_key,
               "dp_login_user": user, "dp_login_password": pwd})
    if r.get("type") != "success":
        raise RuntimeError(f"DepositPhotos login failed: {r.get('error', {}).get('errormsg', r)}")
    return str(r["sessionid"])


def _score(result: Dict, query_words: list[str]) -> int:
    """Score a photo. Higher is better. Negative means reject."""
    title = (result.get("title") or "").lower()
    tags = " ".join(result.get("tags") or []).lower()

    # Hard rejects.
    if any(frag in title for frag in _BLOCKED_TITLE_FRAGMENTS):
        return -99
    if result.get("isIllustration") or result.get("nudity"):
        return -99
    width = int(result.get("width") or 0)
    if width < _MIN_WIDTH:
        return -99
    downloads = int(result.get("downloads") or 0)
    if downloads < _MIN_DOWNLOADS:
        return -1  # low signal, but not an outright reject

    score = 0

    # Resolution bonus.
    if width >= 5000:
        score += 2
    elif width >= 4000:
        score += 1

    # Popularity.
    if downloads >= 100:
        score += 2
    elif downloads >= 30:
        score += 1

    # Do the query words appear in the title/tags?
    for word in query_words:
        if len(word) >= 4:
            if word in title:
                score += 2
            elif word in tags:
                score += 1

    # Editorial photos tend to be more authentic.
    if result.get("iseditorial") or result.get("is_editorial"):
        score += 1

    return score


def _is_usable(result: Dict) -> bool:
    title = (result.get("title") or "").lower()
    return not any(frag in title for frag in _BLOCKED_TITLE_FRAGMENTS)


def search(query: str, count: int = 8, orientation: str = "horizontal") -> List[Dict[str, Any]]:
    """Search DepositPhotos, score, and rank the results.

    Each result: {id, title, score, preview_url, width, downloads}
    Only photos scoring at or above _MIN_SCORE are returned.
    """
    api_key = _api_key()
    # Over-fetch so there's still `count` left after filtering.
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
        raise RuntimeError(f"DepositPhotos search error: {r.get('error', {}).get('errormsg', r)}")

    results = r.get("result", [])
    if isinstance(results, dict):
        results = list(results.values())

    query_words = query.lower().split()

    # Score and filter.
    scored = []
    for v in results:
        s = _score(v, query_words)
        if s >= _MIN_SCORE:
            scored.append((s, v))

    # Sort by score, best first.
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
    """Download the licensed XL file, return its local path."""
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
        raise RuntimeError(f"DepositPhotos download error ({asset_id}): {err.get('errormsg', err)}")

    dl_url = r["downloadLink"]
    out_dir = Path(dest_dir) if dest_dir else Path(tempfile.mkdtemp(prefix="pictovap_deposit_"))
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"deposit_{asset_id}.jpg"

    req = urllib.request.Request(dl_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())

    return str(dest)


def search_and_download(
    query: str,
    count: int = 4,
    dest_dir: Optional[str] = None,
    orientation: str = "horizontal",
) -> List[str]:
    """Combined search + download. Returns a list of local file paths."""
    session_id = _login()
    results = search(query, count=count, orientation=orientation)
    if not results:
        raise RuntimeError(f"No DepositPhotos results found for: {query!r}")

    paths = []
    for r in results[:count]:
        try:
            path = download(r["id"], session_id, dest_dir=dest_dir)
            paths.append(path)
        except RuntimeError as e:
            print(f"  Skipped ({r['id']}): {e}")
    return paths


def search_candidates(query: str, count: int = 8) -> List[Dict[str, Any]]:
    """ImageSourceAdapter-conformant candidate search (no download).

    Returns the standard candidate dict shape without fetching the actual
    image bytes; the pipeline downloads only selected images. Returns an
    empty list (rather than raising) when DEPOSIT_API_KEY is not set, so
    this adapter degrades gracefully when unconfigured.
    """
    try:
        results = search(query, count=count)
    except RuntimeError:
        return []
    return [
        {
            "id": f"deposit-{r['id']}",
            "filename": f"deposit_{r['id']}.jpg",
            "provider": "depositphotos",
            "source_type": "api",
            "local_path": None,
            "source_url": r.get("preview_url"),
            "license": "editorial",
            "attribution": None,
            "keywords": [w for w in (r.get("title") or "").split() if w],
            "width": r.get("width", 0),
            "height": 0,
        }
        for r in results
    ]


class DepositPhotosSource:
    """Class wrapper around the module-level DepositPhotos functions.

    `search`/`download`/`search_and_download`/`search_candidates` above are
    kept as free functions since they predate the ImageSourceAdapter
    protocol and existing callers rely on them directly. This thin wrapper
    exists so DepositPhotos can be instantiated and checked the same way as
    `LocalFolderSource` and `UnsplashSource`
    (`issubclass(DepositPhotosSource, ImageSourceAdapter)`), and is the
    preferred entry point for new code.
    """

    def search_candidates(self, query: str, count: int) -> List[Dict[str, Any]]:
        return search_candidates(query, count)


__all__ = [
    "search",
    "download",
    "search_and_download",
    "search_candidates",
    "DepositPhotosSource",
    "_login",
]
