"""Selection helpers exposed from the canonical engine package."""

from __future__ import annotations

from typing import Any, Dict, List

import json
from src.core.processor import get_vil_images
from src.main import load_vil_images_from_index_for_post, search_semantic_assets
from src.pictova.config import get_visual_memory_db_path


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
            return {"source": "semantic", "query": location_query or "", "content_filter": content_filter, "files": files}

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

        # 3. DepositPhotos — hâlâ eksikse
        if len(files) < _count:
            need = _count - len(files)
            base_q = location_query or _extract_location(post_context)
            enriched_q = _enrich_query_for_theme(base_q, post_context, content_filter)
            dep_files = _deposit_search_download(query=enriched_q, count=need)
            files = files + dep_files

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
        return {
            "source": "unsplash",
            "query": query or "",
            "content_filter": None,
            "files": [],
        }

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
) -> str:
    """Post temasına göre arama sorgusuna modifier ekler."""
    text = " ".join([
        query.lower(),
        str(post_context.get("title") or "").lower(),
        str(post_context.get("slug") or "").lower(),
        str(content_filter or "").lower(),
    ])

    if any(kw in text for kw in _THEME_NIGHT_KEYWORDS):
        # Gece teması: gündüz fotoğraf gelmesin
        if "night" not in query and "gece" not in query:
            return query + " night"
    elif any(kw in text for kw in _THEME_NATURE_KEYWORDS):
        if "nature" not in query and "landscape" not in query:
            return query + " landscape"
    elif any(kw in text for kw in _THEME_BEACH_KEYWORDS):
        if "beach" not in query and "coast" not in query:
            return query + " coast"

    return query


def _deposit_search_download(query: str, count: int) -> list[str]:
    """DepositPhotos'tan ara + indir. Hata olursa boş liste döner."""
    try:
        from src.pictova.providers.deposit import search_and_download
        return search_and_download(query=query, count=count)
    except Exception as e:
        print(f"  ⚠ DepositPhotos atlandı: {e}")
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
