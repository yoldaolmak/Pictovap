"""Selection helpers exposed from the canonical engine package."""

from __future__ import annotations

from typing import Any, Dict

import json
from pictova.core.processor import get_vil_images
from pictova.main import load_vil_images_from_index_for_post, search_semantic_assets
from pictova.config import get_visual_memory_db_path


def resolve_source_images(
    *,
    source: str,
    count: int | None,
    name: str | None,
    query: str | None,
    location_query: str | None,
    content_filter: str | None,
    post_context: Dict[str, Any],
) -> Dict[str, Any]:
    _count = count or 5

    if source == "auto":
        # 1. Lokal fotoğraflar (semantic search)
        files = search_semantic_assets(
            location_query=location_query or _extract_location(post_context),
            count=_count,
            content_filter=content_filter,
            post_context=post_context,
        )
        if len(files) >= _count:
            return {
                "source": "semantic",
                "query": location_query or "",
                "content_filter": content_filter,
                "files": files,
            }

        # 2. iCloud aday fotoğraflar — önce destination index, sonra FTS fallback
        need = _count - len(files)
        loc_q = location_query or _extract_location(post_context)
        icloud_uuids = _destination_index_uuids(loc_q, need)
        if not icloud_uuids:
            icloud = search_semantic_assets(
                location_query=loc_q,
                count=need,
                content_filter=content_filter,
                post_context=post_context,
                include_icloud=True,
            )
            icloud_uuids = [f for f in icloud if f.startswith("icloud://")]
        if icloud_uuids:
            files = files + icloud_uuids[:need]

        # 3. Dış kaynaklar: %75-80 DepositPhotos, %20-25 Unsplash
        if len(files) < _count:
            need = _count - len(files)
            base_q = location_query or _extract_location(post_context)

            # Oran hesabı: %25 Unsplash (en az 1), kalanı Deposit
            uns_target = max(1, int(need * 0.25)) if need >= 4 else (1 if need > 1 else 0)
            dep_target = need - uns_target

            dep_q = _enrich_query_for_theme(base_q, post_context, content_filter, source="deposit")
            uns_q = _enrich_query_for_theme(base_q, post_context, content_filter, source="unsplash")

            # Önce Deposit'i çek
            dep_files = _deposit_search_download(query=dep_q, count=dep_target) if dep_target > 0 else []

            # Deposit bulamadıysa eksiği Unsplash'a devret
            missing_dep = dep_target - len(dep_files)
            if missing_dep > 0:
                uns_target += missing_dep

            # Unsplash'ı çek
            uns_files = _unsplash_search_download(query=uns_q, count=uns_target) if uns_target > 0 else []

            # Unsplash bulamadıysa ve Deposit daha önce eksik kalmadıysa Deposit'ten tekrar
            # şansımızı denemek zor çünkü offset yok. O yüzden listeleri birleştiriyoruz.
            # Interlace (Karıştırma): Arka arkaya aynı kaynaktan gelmemesi için
            merged = []
            for d, u in zip(dep_files, uns_files):
                merged += [d, u]
            merged += dep_files[len(uns_files):] + uns_files[len(dep_files):]

            files = files + merged

        return {"source": "auto", "query": location_query or "", "content_filter": content_filter, "files": files}

    if source == "semantic":
        files = search_semantic_assets(
            location_query=location_query or "",
            count=_count,
            content_filter=content_filter,
            post_context=post_context,
        )
        return {
            "source": "semantic",
            "query": location_query or "",
            "content_filter": content_filter,
            "files": files,
        }

    if source == "vil":
        files = load_vil_images_from_index_for_post(
            count=count,
            name=name,
            post_context=post_context,
        )
        if not files:
            files = get_vil_images(count=count, name=name)
        return {
            "source": "vil",
            "query": name or "",
            "content_filter": None,
            "files": files,
        }

    if source == "deposit":
        loc_q = location_query or query or _extract_location(post_context)
        enriched_q = _enrich_query_for_theme(loc_q, post_context, content_filter)
        files = _deposit_search_download(query=enriched_q, count=_count)
        return {"source": "deposit", "query": enriched_q, "content_filter": None, "files": files}

    if source == "local":
        # Doğrudan dosya yolları listesi — query'yi "," veya "\n" ayıracı ile al
        raw = query or ""
        paths = [p.strip() for p in raw.replace("\n", ",").split(",") if p.strip()]
        # post_context'te "files" varsa onu da al
        extra = post_context.get("files") or []
        if isinstance(extra, list):
            paths = paths + [str(f) for f in extra]
        paths = paths[:_count]
        return {"source": "local", "query": raw, "content_filter": None, "files": paths}

    if source == "unsplash":
        loc_q = location_query or query or _extract_location(post_context)
        enriched_q = _enrich_query_for_theme(loc_q, post_context, content_filter, source="unsplash")
        files = _unsplash_search_download(query=enriched_q, count=_count)
        return {"source": "unsplash", "query": enriched_q, "content_filter": None, "files": files}

    raise ValueError(f"Unsupported source: {source}")


_THEME_NIGHT_KEYWORDS = {
    "gece hayatı", "nightlife", "gece kulübü", "bar ", "barlar", "eğlence",
    "party", "club ", "disco", "meyhane", "taverna", "pub ",
}
_THEME_NATURE_KEYWORDS = {
    "doğa", "yayla", "orman", "dağ", "kanyonu", "şelale", "vadisi",
    "nature", "forest", "mountain", "canyon", "waterfall",
}
_THEME_BEACH_KEYWORDS = {
    "plaj", "koy", "deniz", "sahil", "beach", "bay", "coast",
}


def _enrich_query_for_theme(
    query: str,
    post_context: Dict[str, Any],
    content_filter: str | None,
    *,
    source: str = "deposit",
) -> str:
    """Post temasına göre sorguya modifier ekler.

    source='unsplash': atmosferik modifier (sunset/evening/landscape)
    source='deposit' : spesifik modifier (night/coast/landscape)
    """
    text = " ".join([
        query.lower(),
        str(post_context.get("title") or "").lower(),
        str(post_context.get("slug") or "").lower(),
        str(content_filter or "").lower(),
    ])

    if any(kw in text for kw in _THEME_NIGHT_KEYWORDS):
        if source == "unsplash":
            if "sunset" not in query and "evening" not in query:
                return query + " sunset"
        else:
            if "night" not in query and "gece" not in query:
                return query + " night"
    elif any(kw in text for kw in _THEME_NATURE_KEYWORDS):
        if "landscape" not in query and "nature" not in query:
            return query + " landscape"
    elif any(kw in text for kw in _THEME_BEACH_KEYWORDS):
        if "beach" not in query and "coast" not in query:
            return query + " coast"

    return query


def _deposit_search_download(query: str, count: int) -> list[str]:
    """DepositPhotos'tan ara + indir. Hata olursa boş liste döner."""
    try:
        from pictova.providers.deposit import search_and_download
        return search_and_download(query=query, count=count)
    except Exception as e:
        print(f"  ⚠ DepositPhotos atlandı: {e}")
        return []


def _unsplash_search_download(query: str, count: int) -> list[str]:
    """Unsplash'tan ara + indir. Hata olursa boş liste döner."""
    try:
        from pictova.providers.unsplash import YOUnsplashDownloader
        d = YOUnsplashDownloader()
        # Kalite filtresi: min 3000px genişlik, önce likes>0
        results = d.search(query, count=count * 3)
        scored = []
        for r in results:
            w = r.get("width", 0)
            likes = r.get("likes", 0)
            if w < 3000:
                continue
            score = likes + (2 if w >= 5000 else 0)
            scored.append((score, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        best = [r for _, r in scored[:count]]
        if not best:
            return []
        # İndir
        downloaded = []
        for i, r in enumerate(best, 1):
            try:
                import tempfile
                import requests as _req
                import pathlib as _pl
                dl_url = r["links"]["download"]
                import os
                access_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
                resp = _req.get(dl_url, headers={"Authorization": f"Client-ID {access_key}"}, timeout=30)
                resp.raise_for_status()
                import re
                photographer = r.get("user", {}).get("name", "Bilinmiyor")
                photographer_safe = re.sub(r'[^a-zA-Z0-9]', '_', photographer)
                slug = query.split()[0].lower()
                dest = _pl.Path(tempfile.gettempdir()) / "pictova_unsplash" / f"{slug}-{i}-by-{photographer_safe}.jpg"
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(resp.content)
                downloaded.append(str(dest))
            except Exception as e:
                print(f"  ⚠ Unsplash indirme hatası ({i}): {e}")
        return downloaded
    except Exception as e:
        print(f"  ⚠ Unsplash atlandı: {e}")
        return []


def _extract_location(post_context: Dict[str, Any]) -> str:
    """Post slug/title'dan konum token'ı çıkar."""
    slug = str(post_context.get("slug") or "").replace("-", " ")
    title = str(post_context.get("title") or "")
    return slug or title


def _destination_index_uuids(query: str, count: int) -> list[str]:
    """Destination index JSON'dan en iyi UUID'leri çek."""
    try:
        idx_path = get_visual_memory_db_path().parent / "destination_index.json"
        if not idx_path.exists():
            return []
        index = json.loads(idx_path.read_text(encoding="utf-8"))
        q_lower = query.lower()
        # İsim eşleşmesi (prefix veya içeriyor)
        for dest_name, uuids in index.items():
            if q_lower in dest_name.lower() or dest_name.lower() in q_lower:
                return [f"icloud://{u}" for u in uuids[:count]]
    except Exception:
        pass
    return []


__all__ = ["load_vil_images_from_index_for_post", "resolve_source_images", "search_semantic_assets"]
