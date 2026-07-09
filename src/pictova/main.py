#!/usr/bin/env python3
from __future__ import annotations

"""
YO OS Orchestrator — Main command handler
Parses user command and orchestrates full pipeline
"""

import re
import json
import os
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from pictova.core.media_quality import normalize_text, validate_metadata, validate_processed_asset
from pictova.utils.config import get_vil_dir, get_visual_memory_db_path, load_project_env

load_project_env()

from pictova.core.media_publish import build_publish_slug_candidates, embed_metadata, ensure_publish_path, ensure_unique_slug
from pictova.core.database import VisualMemoryComponent, VisualMemoryConfig, query_asset_from_visual_memory
from pictova.core.processor import YOImageProcessor, get_vil_images
from pictova.core.metadata_generator import (
    YOMetadataGenerator,
    build_basic_metadata,
)
from pictova.services.wordpress import fetch_post_context, upload_images_batch

try:
    from pictova.core.cloud_vision import YOCloudVisionClient, generate_metadata_for_files as generate_gv_metadata
except ImportError:
    generate_metadata_for_files = None


# ── Semantic arama yardımcıları ──────────────────────────────────────────────

def _ascii_normalize(text: str) -> str:
    """Türkçe harfleri ASCII'ye çevir, küçük harf yap — path LIKE araması için."""
    result = str(text or "")
    for src, dst in [
        ("İ","I"),("Ş","S"),("Ç","C"),("Ğ","G"),("Ü","U"),("Ö","O"),
        ("ş","s"),("ç","c"),("ğ","g"),("ü","u"),("ö","o"),("ı","i"),
    ]:
        result = result.replace(src, dst)
    return result.lower()


# İçerik filtresi → SQL WHERE parçası (OR mantığıyla, GCV sonrası otomatik zenginleşir)
CONTENT_FILTER_SQL: dict[str, str] = {
    "insan":    "(activity IN ('walking','sightseeing','portrait','swimming')"
                " OR vision_labels_json LIKE '%person%'"
                " OR vision_labels_json LIKE '%people%'"
                " OR vision_labels_json LIKE '%face%'"
                " OR vision_labels_json LIKE '%crowd%')",
    "portrait": "(activity='portrait' OR vision_labels_json LIKE '%portrait%')",
    "sokak":    "(scene='street'"
                " OR vision_labels_json LIKE '%street%'"
                " OR vision_labels_json LIKE '%alley%'"
                " OR vision_labels_json LIKE '%road%')",
    "mimari":   "(scene='landmark'"
                " OR vision_labels_json LIKE '%building%'"
                " OR vision_labels_json LIKE '%architecture%'"
                " OR vision_labels_json LIKE '%church%'"
                " OR vision_labels_json LIKE '%mosque%')",
    "doga":     "(scene IN ('nature','landscape')"
                " OR vision_labels_json LIKE '%nature%'"
                " OR vision_labels_json LIKE '%forest%'"
                " OR vision_labels_json LIKE '%mountain%')",
    "deniz":    "(scene IN ('sahil','kiyi')"
                " OR vision_labels_json LIKE '%sea%'"
                " OR vision_labels_json LIKE '%ocean%'"
                " OR vision_labels_json LIKE '%beach%'"
                " OR vision_labels_json LIKE '%coast%')",
    "gece":     "(vision_labels_json LIKE '%night%' OR vision_labels_json LIKE '%dark%')",
    "pazar":    "(scene='market'"
                " OR vision_labels_json LIKE '%market%'"
                " OR vision_labels_json LIKE '%bazaar%')",
    "tapinak":  "(scene='landmark'"
                " OR vision_labels_json LIKE '%temple%'"
                " OR vision_labels_json LIKE '%mosque%'"
                " OR vision_labels_json LIKE '%pagoda%')",
    "yiyecek":  "(vision_labels_json LIKE '%food%' OR vision_labels_json LIKE '%dish%')",
    "tekne":    "(vision_labels_json LIKE '%boat%' OR vision_labels_json LIKE '%ship%'"
                " OR vision_labels_json LIKE '%vessel%')",
}

# Takma adlar
_FILTER_ALIASES: dict[str, str] = {
    "insan": "insan", "insanlar": "insan", "kisi": "insan", "kisiler": "insan",
    "people": "insan", "person": "insan", "adam": "insan", "kadin": "insan",
    "portrait": "portrait", "portre": "portrait",
    "sokak": "sokak", "cadde": "sokak", "street": "sokak",
    "mimari": "mimari", "bina": "mimari", "yapi": "mimari", "architecture": "mimari",
    "doga": "doga", "nature": "doga", "orman": "doga", "dag": "doga",
    "deniz": "deniz", "sahil": "deniz", "beach": "deniz", "sea": "deniz",
    "gece": "gece", "night": "gece",
    "pazar": "pazar", "market": "pazar", "bazaar": "pazar", "carsi": "pazar",
    "tapinak": "tapinak", "cami": "tapinak", "mosque": "tapinak", "kilise": "tapinak",
    "yemek": "yiyecek", "food": "yiyecek", "yiyecek": "yiyecek",
    "tekne": "tekne", "boat": "tekne", "gemi": "tekne",
}


def _row_value(row: Any, key: str, default: Any = None) -> Any:
    """Read sqlite3.Row and dict values through one safe interface."""
    try:
        value = row[key]
    except (KeyError, IndexError, TypeError):
        getter = getattr(row, "get", None)
        value = getter(key, default) if getter else default
    return default if value is None else value


def _capture_time(row: Any) -> datetime | None:
    raw = str(_row_value(row, "created_at", "") or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _distance_meters(left: Any, right: Any) -> float | None:
    try:
        lat1 = float(_row_value(left, "latitude"))
        lon1 = float(_row_value(left, "longitude"))
        lat2 = float(_row_value(right, "latitude"))
        lon2 = float(_row_value(right, "longitude"))
    except (TypeError, ValueError):
        return None
    mean_lat = math.radians((lat1 + lat2) / 2)
    x = math.radians(lon2 - lon1) * math.cos(mean_lat)
    y = math.radians(lat2 - lat1)
    return 6_371_000 * math.sqrt(x * x + y * y)


def _same_capture_burst(left: Any, right: Any) -> bool:
    """Treat near-simultaneous shots from the same position as one candidate."""
    left_time = _capture_time(left)
    right_time = _capture_time(right)
    if left_time is None or right_time is None:
        return False
    try:
        seconds = abs((left_time - right_time).total_seconds())
    except TypeError:
        return False
    distance = _distance_meters(left, right)
    return seconds <= 120 and distance is not None and distance <= 250


def _perceptual_hash(path: str, hash_size: int = 8) -> int | None:
    """Return a small dHash for inexpensive visual near-duplicate filtering."""
    if not path:
        return None
    try:
        from PIL import Image, ImageOps

        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert("L")
            resampling = getattr(Image, "Resampling", Image).LANCZOS
            pixels = list(image.resize((hash_size + 1, hash_size), resampling).getdata())
    except Exception:
        return None

    value = 0
    width = hash_size + 1
    for row in range(hash_size):
        offset = row * width
        for column in range(hash_size):
            value = (value << 1) | int(pixels[offset + column] > pixels[offset + column + 1])
    return value


def _contains_people(row: Any) -> bool:
    try:
        people = json.loads(str(_row_value(row, "people_json", "[]") or "[]"))
    except (TypeError, ValueError, json.JSONDecodeError):
        people = []
    if isinstance(people, list) and people:
        return True
    try:
        labels = json.loads(str(_row_value(row, "apple_labels_json", "[]") or "[]"))
    except (TypeError, ValueError, json.JSONDecodeError):
        labels = []
    return any(str(label).lower() in {"person", "people", "face", "portrait"} for label in labels)


def _select_diverse_rows(
    rows: list[Any],
    count: int,
    *,
    include_icloud: bool = False,
    allow_people: bool = False,
) -> list[Any]:
    """Keep quality order while suppressing burst and perceptual duplicates."""
    selected: list[Any] = []
    selected_hashes: list[int] = []
    seen_assets: set[str] = set()

    for row in rows:
        source_path = str(_row_value(row, "source_path", "") or "")
        source_id = str(_row_value(row, "source_id", "") or "")
        asset_key = source_path or (f"icloud://{source_id}" if include_icloud and source_id else "")
        if not asset_key or asset_key in seen_assets:
            continue
        if not allow_people and _contains_people(row):
            continue
        if any(_same_capture_burst(row, previous) for previous in selected):
            continue

        image_hash = _perceptual_hash(source_path) if source_path and Path(source_path).exists() else None
        if image_hash is not None and any(bin(image_hash ^ previous).count("1") <= 8 for previous in selected_hashes):
            continue

        selected.append(row)
        seen_assets.add(asset_key)
        if image_hash is not None:
            selected_hashes.append(image_hash)
        if len(selected) >= count:
            break

    return selected


def _expand_trip_candidates(conn: Any, seed_rows: list[Any], count: int, *, include_icloud: bool) -> list[Any]:
    """Expand sparse text matches with nearby assets captured on the same trip days."""
    coordinates = []
    dates = set()
    for row in seed_rows:
        created_at = str(_row_value(row, "created_at", "") or "")
        if len(created_at) >= 10:
            dates.add(created_at[:10])
        try:
            coordinates.append((float(_row_value(row, "latitude")), float(_row_value(row, "longitude"))))
        except (TypeError, ValueError):
            continue

    if not coordinates or not dates:
        return []

    min_lat = min(lat for lat, _ in coordinates) - 0.03
    max_lat = max(lat for lat, _ in coordinates) + 0.03
    min_lon = min(lon for _, lon in coordinates) - 0.04
    max_lon = max(lon for _, lon in coordinates) + 0.04
    trip_dates = sorted(dates)[:7]
    date_placeholders = ",".join("?" for _ in trip_dates)
    local_clause = "" if include_icloud else "AND source_path != ''"
    sql = f"""
        SELECT source_path, filename, quality_score, selection_score,
               activity, scene, location, city, state_province,
               country, title, description, summary, orientation,
               ai_keywords_json, source_id, created_at, latitude, longitude,
               vision_scan_status, people_json, apple_labels_json
        FROM asset_index
        WHERE is_personal = 0
          {local_clause}
          AND latitude BETWEEN ? AND ?
          AND longitude BETWEEN ? AND ?
          AND substr(created_at, 1, 10) IN ({date_placeholders})
        ORDER BY
          (CASE WHEN vision_scan_status = 'done' THEN 1 ELSE 0 END) DESC,
          selection_score DESC, quality_score DESC, created_at ASC
        LIMIT ?
    """
    params = [min_lat, max_lat, min_lon, max_lon, *trip_dates, max(count * 20, 100)]
    try:
        return conn.execute(sql, params).fetchall()
    except Exception:
        return []


def search_semantic_assets(
    location_query: str,
    count: int,
    content_filter: str | None = None,
    post_context: Dict | None = None,
    include_icloud: bool = False,
) -> list[str]:
    """
    Lokasyon sorgusu + içerik filtresiyle HDD'den fotoğraf bul.

    location_query: "madura adası", "alaçatı", "roma trastevere" vb.
    content_filter: "insan", "sokak", "mimari" vb. — None = filtre yok
    Döndürür: mevcut dosya path'lerinin listesi
    """
    import sqlite3

    db_path = get_visual_memory_db_path()
    if not db_path.exists():
        return []

    # Coğrafi alias genişletme
    try:
        from pictova.engine.geo_aliases import expand_query
        expanded_terms = expand_query(location_query)
    except Exception:
        expanded_terms = [location_query]

    # Sorguyu normalize et — Türkçe karakterleri koru, FTS unicode61 halleder
    # Tüm expanded terimleri birleştir
    combined_query = " ".join(expanded_terms[:4])  # ilk 4 terim
    query_clean = re.sub(r'[^\w\s]', ' ', combined_query, flags=re.UNICODE).strip()
    tokens = [t for t in re.split(r"\s+", query_clean) if len(t) >= 3]
    if not tokens:
        return []

    filter_keys = {
        _FILTER_ALIASES.get(_ascii_normalize(item.strip()), "")
        for item in str(content_filter or "").split(",")
        if item.strip()
    }
    allow_people = bool(filter_keys & {"insan", "portrait"})

    # FTS5 MATCH sorgusu — her token AND mantığıyla, prefix match için *
    fts_query = " ".join(f'"{t}"*' for t in tokens)

    # İçerik filtresi SQL (Dinamik)
    content_sql_parts = []
    content_sql_params = []
    
    if content_filter:
        for raw_item in str(content_filter).split(','):
            item = raw_item.strip().lower()
            if not item:
                continue
                
            norm_item = _ascii_normalize(item)
            
            if norm_item == "dikey":
                content_sql_parts.append("a.orientation = 'portrait'")
            elif norm_item == "yatay":
                content_sql_parts.append("a.orientation = 'landscape'")
            else:
                canonical_cf = _FILTER_ALIASES.get(norm_item)
                if canonical_cf and canonical_cf in CONTENT_FILTER_SQL:
                    content_sql_parts.append(CONTENT_FILTER_SQL[canonical_cf])
                else:
                    # Serbest metin -> keyword / people / description araması
                    content_sql_parts.append("(a.ai_keywords_json LIKE ? OR a.description LIKE ? OR a.people_json LIKE ?)")
                    like_val = f"%{item}%"
                    content_sql_params.extend([like_val, like_val, like_val])
                    
    content_filter_clause = f"AND ({' AND '.join(content_sql_parts)})" if content_sql_parts else ""

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # FTS ile eşleşen source_id'leri bul, asset_index ile JOIN et
        sql = f"""
            SELECT a.source_path, a.filename, a.quality_score, a.selection_score,
                   a.activity, a.scene, a.location, a.city, a.state_province,
                   a.country, a.title, a.description, a.summary, a.orientation,
                   a.ai_keywords_json, a.source_id, a.created_at, a.latitude,
                   a.longitude, a.vision_scan_status, a.people_json,
                   a.apple_labels_json
            FROM asset_search s
            JOIN asset_index a ON a.source_id = s.source_id
            WHERE s.document MATCH ?
              AND a.is_personal = 0
              {"" if include_icloud else "AND a.source_path != ''"}
              {content_filter_clause}
            ORDER BY
              (CASE WHEN a.vision_scan_status = 'done' THEN 1 ELSE 0 END) DESC,
              a.selection_score DESC, a.quality_score DESC
            LIMIT ?
        """
        try:
            params = [fts_query] + content_sql_params + [max(count * 4, 30)]
            rows = conn.execute(sql, params).fetchall()
        except Exception as e:
            # FTS MATCH hatası (özel karakter vb.) → LIKE fallback
            rows = []

        # FTS sonuç yetersizse LIKE fallback (tek token, city/state_province)
        if len(rows) < count and tokens:
            like_clauses = " OR ".join(
                f"LOWER(COALESCE(city,'')) LIKE ? OR LOWER(COALESCE(state_province,'')) LIKE ?"
                for _ in tokens
            )
            like_params = [f"%{t.lower()}%" for t in tokens for _ in range(2)]
            
            # LIKE fallback için content filter alanlarındaki a. öneklerini kaldır
            fallback_content_clause = content_filter_clause.replace('a.', '') if content_filter_clause else ''
            
            fb_sql = f"""
                SELECT source_path, filename, quality_score, selection_score,
                       activity, scene, location, city, state_province,
                       country, title, description, summary, orientation,
                       ai_keywords_json, source_id, created_at, latitude,
                       longitude, vision_scan_status, people_json,
                       apple_labels_json
                FROM asset_index
                WHERE ({like_clauses}) AND is_personal = 0
                  {fallback_content_clause}
                ORDER BY selection_score DESC, quality_score DESC
                LIMIT ?
            """
            seen = {r["source_path"] for r in rows}
            fb_params = like_params + content_sql_params + [max(count * 4, 30)]
            fb_rows = conn.execute(fb_sql, fb_params).fetchall()
            rows = list(rows) + [r for r in fb_rows if r["source_path"] not in seen]

        if not content_filter and len(_select_diverse_rows(
            list(rows), count, include_icloud=include_icloud, allow_people=allow_people
        )) < count:
            seen_ids = {str(_row_value(row, "source_id", "")) for row in rows}
            trip_rows = _expand_trip_candidates(conn, list(rows), count, include_icloud=include_icloud)
            rows = list(rows) + [
                row for row in trip_rows
                if str(_row_value(row, "source_id", "")) not in seen_ids
            ]
    finally:
        conn.close()

    # Post context varsa hero scoring ile yeniden sırala
    if post_context and rows:
        rows = sorted(rows, key=lambda r: _hero_score(r, post_context), reverse=True)

    paths: list[str] = []
    for row in _select_diverse_rows(
        list(rows), count, include_icloud=include_icloud, allow_people=allow_people
    ):
        src = str(_row_value(row, "source_path", "") or "")
        if not src:
            if include_icloud:
                # iCloud source_id (UUID) döndür — üst katman indirir
                paths.append(f"icloud://{_row_value(row, 'source_id', '')}")
            continue
        paths.append(src)
    return paths


def load_vil_images_from_index(count: int | None = None, name: str | None = None) -> List[str]:
    return load_vil_images_from_index_for_post(count=count, name=name, post_context={})


def _tokenize_focus(text: str) -> list[str]:
    return [
        token for token in re.findall(r"[a-zA-Z0-9çğıöşüÇĞİÖŞÜ]+", str(text or "").lower())
        if len(token) >= 3
    ]


def _hero_score(row: Dict, post_context: Dict) -> float:
    score = float(_row_value(row, "quality_score", 0) or 0)
    title_tokens = _tokenize_focus(post_context.get("title", ""))
    slug_tokens = _tokenize_focus(str(post_context.get("slug", "")).replace("-", " "))
    focus_tokens = title_tokens[:6] + [token for token in slug_tokens if token not in title_tokens][:4]
    try:
        import json as _json
        ai_kws = " ".join(_json.loads(_row_value(row, "ai_keywords_json", "[]") or "[]"))
    except Exception:
        ai_kws = ""
    haystack = " ".join(
        [
            str(_row_value(row, "filename", "") or "").lower(),
            str(_row_value(row, "title", "") or "").lower(),
            str(_row_value(row, "description", "") or "").lower(),
            str(_row_value(row, "location", "") or "").lower(),
            str(_row_value(row, "activity", "") or "").lower(),
            str(_row_value(row, "summary", "") or "").lower(),
            ai_kws.lower(),
        ]
    )
    overlap = sum(1 for token in focus_tokens if token in haystack)
    score += overlap * 1.5
    # vision scan tamamlanmış fotoğraflara bonus
    if ai_kws:
        score += 0.3
    if _row_value(row, "orientation", "") == "landscape":
        score += 0.75
    if _row_value(row, "scene", "") in {"landmark", "street", "nature"}:
        score += 0.5
    if _row_value(row, "activity", "") in {"unknown", "portrait"}:
        score -= 0.25
    return score


def load_vil_images_from_index_for_post(
    *,
    count: int | None = None,
    name: str | None = None,
    post_context: Dict | None = None,
) -> List[str]:
    vil_dir = get_vil_dir()
    component = VisualMemoryComponent(
        VisualMemoryConfig(
            database_path=get_visual_memory_db_path(),
            external_roots=[vil_dir],
            scan_photos_library=False,
        )
    )
    rows = component.list_assets(
        limit=max(count or 20, 20),
        source_root=vil_dir,
        filename_query=name,
        source_types=("external_hdd",),
    )
    if post_context:
        rows = sorted(rows, key=lambda row: _hero_score(row, post_context), reverse=True)
    paths: list[str] = []
    for row in rows:
        path = Path(row["source_path"])
        if path.exists():
            paths.append(str(path))
    return paths[: count or len(paths)]


class YOCommandParser:
    """Parse YO commands:
      "5 foto yo 21312"                           → son 5 resim, yoldaolmak
      "3 foto yo 21312 GE"                        → son 3, gezievreni
      "unsplash:zadar sea 3 foto yo 21312"        → Unsplash'tan 3 resim
      "kalenderis yo 21312"                       → isimle eşleşen resimler
      "madura adası 5 foto insan yo 21312"        → semantic arama + upload
      "madura adası 5 foto insan"                 → semantic arama, yerel çıktı
      "Post: 1009 içinde insan olan 5 foto"       → post bağlamıyla semantic arama
    """

    PATTERN_COUNT        = r"^(\d+)\s+foto\s+yo\s+(\d+)(?:\s+(\w+))?$"
    PATTERN_VIL_POST     = r"^vil\s+(\d+)\s+post\s+(\d+)(?:\s+(\w+))?$"
    PATTERN_UNSPLASH     = r"^unsplash:([^0-9]+)\s+(\d+)\s+foto\s+yo\s+(\d+)(?:\s+(\w+))?$"
    # Semantic + upload: "madura adası 5 foto insan yo 21312 [GE]"
    PATTERN_SEMANTIC_POST = r"^(.+?)\s+(\d+)\s+foto(?:\s+(?!yo\b)(\S+))?\s+yo\s+(\d+)(?:\s+(\w+))?$"
    PATTERN_NAME         = r"^(.+?)\s+yo\s+(\d+)(?:\s+(\w+))?$"
    # Semantic yerel: "madura adası 5 foto insan"
    PATTERN_SEMANTIC_ONLY = r"^(.+?)\s+(\d+)\s+foto(?:\s+(\S+))?$"
    # Post bağlamı: "Post: 1009 içinde insan olan 5 foto"
    PATTERN_POST_QUERY   = r"^[Pp]ost:\s*(\d+)\s+(.+?)\s+(\d+)\s+foto\w*$"

    SITE_ALIASES = {
        "yo": "yoldaolmak",
        "ge": "gezievreni",
        "gd": "gezgindunyasi",
        "yoldaolmak": "yoldaolmak",
        "gezievreni": "gezievreni",
        "gezgindunyasi": "gezgindunyasi",
    }
    VALID_SITES = list(SITE_ALIASES.values())

    @classmethod
    def parse(cls, command: str) -> Optional[Dict]:
        command = command.strip()

        # 0a. DepositPhotos: "deposit:bodrum gece 4 foto yo 31818"
        if command.lower().startswith("deposit:"):
            rest = command[8:].strip()
            # rest: "<sorgu> <N> foto yo <post_id>"
            dm = re.match(r"^(.+?)\s+(\d+)\s+foto\s+yo\s+(\d+)(?:\s+(\w+))?$", rest, re.I)
            if dm:
                site = cls.SITE_ALIASES.get((dm.group(4) or "yo").lower())
                if site:
                    return {"count": int(dm.group(2)), "name": None, "post_id": int(dm.group(3)),
                            "site": site, "source": "deposit", "query": dm.group(1).strip()}

        # 0b. Lokal dosya: "local:/path/a.jpg,/path/b.jpg yo 31818"
        if command.lower().startswith("local:"):
            rest = command[6:].strip()
            lm = re.match(r"^(.+?)\s+yo\s+(\d+)(?:\s+(\w+))?$", rest, re.I)
            if lm:
                site = cls.SITE_ALIASES.get((lm.group(3) or "yo").lower())
                if site:
                    return {"count": None, "name": None, "post_id": int(lm.group(2)),
                            "site": site, "source": "local", "query": lm.group(1).strip()}

        # 1. Unsplash: "unsplash:zadar sea 3 foto yo 21312"
        m = re.match(cls.PATTERN_UNSPLASH, command)
        if m:
            site = cls.SITE_ALIASES.get((m.group(4) or "yo").lower())
            if not site:
                return None
            return {"count": int(m.group(2)), "name": None, "post_id": int(m.group(3)),
                    "site": site, "source": "unsplash", "query": m.group(1).strip()}

        # 2. Sayı ile: "5 foto yo 21312"
        m = re.match(cls.PATTERN_COUNT, command)
        if m:
            site = cls.SITE_ALIASES.get((m.group(3) or "yo").lower())
            if not site:
                return None
            return {"count": int(m.group(1)), "name": None, "post_id": int(m.group(2)),
                    "site": site, "source": "vil"}

        # 3. VIL kısa: "VIL 5 post 2345"
        m = re.match(cls.PATTERN_VIL_POST, command, re.I)
        if m:
            site = cls.SITE_ALIASES.get((m.group(3) or "yo").lower())
            if not site:
                return None
            return {"count": int(m.group(1)), "name": None, "post_id": int(m.group(2)),
                    "site": site, "source": "vil"}

        # 4. Post bağlamı: "Post: 1009 içinde insan olan 5 foto"
        m = re.match(cls.PATTERN_POST_QUERY, command)
        if m:
            post_id  = int(m.group(1))
            raw_query = m.group(2).strip()
            count    = int(m.group(3))
            # query'den içerik filtresi çıkar (son kelime filtre olabilir)
            cf, loc = cls._split_filter_from_query(raw_query)
            return {"count": count, "name": None, "post_id": post_id,
                    "site": "yoldaolmak", "source": "semantic",
                    "location_query": loc, "content_filter": cf}

        # 5. Semantic + upload: "madura adası 5 foto insan yo 21312"
        m = re.match(cls.PATTERN_SEMANTIC_POST, command)
        if m:
            location_query = m.group(1).strip()
            count          = int(m.group(2))
            filter_raw     = (m.group(3) or "").strip()
            site           = cls.SITE_ALIASES.get((m.group(5) or "yo").lower())
            if not site:
                return None
            return {"count": count, "name": None, "post_id": int(m.group(4)),
                    "site": site, "source": "semantic",
                    "location_query": location_query,
                    "content_filter": filter_raw or None}

        # 6. İsim ile: "kalenderis yo 21312"
        m = re.match(cls.PATTERN_NAME, command)
        if m:
            name = m.group(1).strip()
            site = cls.SITE_ALIASES.get((m.group(3) or "yo").lower())
            if not site:
                return None
            return {"count": None, "name": name, "post_id": int(m.group(2)),
                    "site": site, "source": "vil"}

        # 7. Semantic yerel: "madura adası 5 foto insan"
        m = re.match(cls.PATTERN_SEMANTIC_ONLY, command)
        if m:
            location_query = m.group(1).strip()
            count          = int(m.group(2))
            filter_raw     = (m.group(3) or "").strip()
            return {"count": count, "name": None, "post_id": None,
                    "site": "yoldaolmak", "source": "semantic",
                    "location_query": location_query,
                    "content_filter": filter_raw or None}

        return None

    @classmethod
    def _split_filter_from_query(cls, query: str) -> tuple[str | None, str]:
        """
        "içinde insan olan" → ("insan", "içinde olan")
        Bilinen filtre keyword'lerini query'den çıkar.
        """
        known = set(_FILTER_ALIASES.keys())
        words = query.split()
        filters_found: list[str] = []
        remaining: list[str] = []
        for w in words:
            if _ascii_normalize(w) in known:
                filters_found.append(w)
            else:
                remaining.append(w)
        cf = filters_found[0] if filters_found else None
        loc = " ".join(remaining).strip() or query
        return cf, loc


class YOOrchestrator:
    """Full pipeline orchestrator"""

    def __init__(self, work_dir: Path = None):
        self.work_dir = work_dir or Path("/tmp/yo_upload_work")
        self.work_dir.mkdir(exist_ok=True)

        self.processor = YOImageProcessor(work_dir=self.work_dir)
        self.log_file = self.work_dir / f"yo_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    def log(self, message: str):
        import sys
        print(message, file=sys.stderr)

    def run_pipeline(
        self,
        count: int = None,
        name: str = None,
        post_id: int = None,
        site: str = "yoldaolmak",
        location_hint: str = "",
        source: str = "vil",
        query: str = None,
        location_query: str = None,
        content_filter: str = None,
        heading: str = None,
        heading_level: int = 0,
        **_ignored,
    ) -> Dict:
        """Run full upload pipeline.

        source="semantic" → location_query + content_filter ile HDD'den ara.
        post_id=None      → yükleme yapma, sadece ~/Downloads/VIL'e işle.
        """
        upload_mode = post_id is not None
        self.log(f"\n{'='*60}")
        self.log(f"YO OS — {'Upload' if upload_mode else 'Local'} Pipeline")
        self.log(f"{'='*60}")
        self.log(f"Site: {site}")
        self.log(f"Post ID: {post_id or '(yerel mod — yükleme yok)'}")
        self.log(f"Source: {source}" + (f" | query: {location_query}" if location_query else ""))
        if content_filter:
            self.log(f"İçerik filtresi: {content_filter}")
        self.log(f"Images: {count}")
        self.log(f"Work dir: {self.work_dir}")

        result = {
            "command": f"{count} foto yo {post_id} {site}",
            "site": site,
            "post_id": post_id,
            "status": "running",
            "steps": {},
        }

        post_context = fetch_post_context(post_id, site=site) if post_id else {}

        # Step 1: Load images (from VIL or Unsplash)
        if source == "unsplash":
            self.log(f"\n📥 STEP 1: Download from Unsplash (query: '{query}')")
            try:
                from pictova.providers.yo_unsplash import YOUnsplashDownloader

                downloader = YOUnsplashDownloader()
                image_files = downloader.download(query, count=count)

                if not image_files:
                    self.log(f"  ✗ No images downloaded")
                    result["status"] = "failed"
                    result["error"] = f"No images found for '{query}'"
                    return result

                result["steps"]["images_loaded"] = {
                    "count": len(image_files),
                    "files": [Path(f).name for f in image_files],
                    "source": "unsplash",
                    "query": query,
                }
                self.log(f"  ✓ Downloaded {len(image_files)} images from Unsplash")

            except Exception as e:
                self.log(f"  ✗ Error: {e}")
                result["status"] = "failed"
                result["error"] = str(e)
                return result

        elif source == "local":
            # Manuel dosya yolları — virgülle ayrılmış ya da query içinde
            raw_paths = query or ""
            image_files = [p.strip() for p in raw_paths.replace("\n", ",").split(",") if p.strip()]
            # post_context'te files listesi varsa ekle
            extra = (post_context or {}).get("files") or []
            if isinstance(extra, list):
                image_files = image_files + [str(f) for f in extra]

            missing = [p for p in image_files if not os.path.exists(p)]
            if missing:
                result["status"] = "failed"
                result["error"] = f"Dosya bulunamadı: {', '.join(missing)}"
                return result
            self.log(f"\n📂 STEP 1: Lokal dosyalar ({len(image_files)} adet)")
            for p in image_files:
                self.log(f"  • {Path(p).name}")

        elif source == "semantic":
            # Semantic HDD arama: location_query + content_filter
            self.log(f"\n🔍 STEP 1: Semantic HDD arama — '{location_query}'" +
                     (f" | filtre: {content_filter}" if content_filter else ""))
            try:
                image_files = search_semantic_assets(
                    location_query=location_query or "",
                    count=count or 5,
                    content_filter=content_filter,
                    post_context=post_context,
                )
                if not image_files:
                    self.log(f"  ✗ '{location_query}' için eşleşen fotoğraf bulunamadı")
                    self.log(f"    İpucu: Index henüz dolmamış olabilir ({location_query!r} path'te geçiyor mu?)")
                    result["status"] = "failed"
                    result["error"] = f"Semantic arama sonuç vermedi: {location_query!r}"
                    return result

                result["steps"]["images_loaded"] = {
                    "count": len(image_files),
                    "files": [Path(f).name for f in image_files],
                    "source": "semantic",
                    "location_query": location_query,
                    "content_filter": content_filter,
                }
                self.log(f"  ✓ {len(image_files)} fotoğraf bulundu")
                for f in image_files:
                    self.log(f"    {Path(f).parent.name}/{Path(f).name}")
            except Exception as e:
                self.log(f"  ✗ Error: {e}")
                result["status"] = "failed"
                result["error"] = str(e)
                return result

        else:
            # Load from VIL (Downloads)
            self.log(f"\n📁 STEP 1: Load images from VIL")
            try:
                image_files = load_vil_images_from_index_for_post(count=count, name=name, post_context=post_context)
                if image_files:
                    self.log(f"  ✓ Loaded {len(image_files)} images from visual_memory index")
                else:
                    self.log(f"  ℹ visual_memory index had no matching assets, fallback to file scan")
                    image_files = get_vil_images(count=count, name=name)
                if not image_files:
                    self.log(f"  ✗ No images found")
                    result["status"] = "failed"
                    result["error"] = "No images in Downloads"
                    return result

                result["steps"]["images_loaded"] = {
                    "count": len(image_files),
                    "files": [Path(f).name for f in image_files],
                }
                self.log(f"  ✓ Loaded {len(image_files)} images")
            except Exception as e:
                self.log(f"  ✗ Error: {e}")
                result["status"] = "failed"
                result["error"] = str(e)
                return result

        # Step 2: Process images (crop, filter, export)
        self.log(f"\n🎨 STEP 2: Process images (crop + YO filter)")
        processed_images = {}
        processed_details = {}
        panoramic_images = {}
        try:
            for src_file in image_files:
                dest_file = self.work_dir / (Path(src_file).stem + "_yo.webp")
                result_data = self.processor.process_image(
                    input_path=src_file,
                    output_path=str(dest_file),
                    auto_saturation=True,
                )

                # Panoramik tespit
                if result_data.get("is_panoramic"):
                    panoramic_images[src_file] = {
                        "output": str(dest_file),
                        "aspect_ratio": result_data.get("aspect_ratio"),
                    }
                    self.log(f"    ⚠️  Panoramik: {Path(src_file).name} ({result_data.get('aspect_ratio'):.2f}:1)")
                else:
                    processed_images[src_file] = str(dest_file)
                    processed_details[str(dest_file)] = result_data

            result["steps"]["images_processed"] = {
                "count": len(processed_images),
                "panoramic_count": len(panoramic_images),
                "output_dir": str(self.work_dir),
            }

            if panoramic_images:
                self.log(f"  ⚠️  Panoramik: {len(panoramic_images)} resim (pillar pages için ayırıldı)")

            self.log(f"  ✓ Processed {len(processed_images)} images (normal post'a)")

            if not processed_images and panoramic_images:
                self.log(f"  ✗ Sadece panoramik resimler var - normal post'a uymuyor!")
                result["status"] = "warning"
                result["warning"] = "All images are panoramic (2.0:1 or wider)"
                return result

        except Exception as e:
            self.log(f"  ✗ Error: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            return result

        # Step 3: Generate metadata (GPT-4 Vision primary)
        self.log(f"\n🧠 STEP 3: Generate semantic metadata")
        metadata_dict = {}

        # Use first image's location hint
        raw_hint = location_hint or Path(image_files[0]).stem.split('_')[0]
        hint = "" if str(raw_hint).strip().lower() in {"depositphotos", "img", "image"} else raw_hint
        self.log(f"  Location hint: {hint}")
        if post_context.get("title"):
            self.log(f"  Post title: {post_context['title']}")

        processed_files = list(processed_images.values())
        metadata_source = "fallback"
        vision_hints_map: dict[str, Dict] = {}

        try:
            client = YOCloudVisionClient()
            self.log(f"  ☁️  Google Vision recognition for {len(processed_files)} images...")
            for file in processed_files:
                analysis = client.analyze(file)
                if analysis.get("success"):
                    vision_hints_map[file] = analysis
                else:
                    self.log(f"    ⚠️  {Path(file).name}: {str(analysis.get('error', 'vision error'))[:160]}")
            if vision_hints_map:
                self.log(f"  ✓ Google Vision recognition: {len(vision_hints_map)} images")
        except Exception as e:
            self.log(f"  ⚠️  Google Vision error: {str(e)[:80]}")

        def fill_with_generator(generator: YOMetadataGenerator, label: str) -> int:
            added = 0
            missing_files = [f for f in processed_files if f not in metadata_dict]
            if not missing_files:
                return 0
            self.log(f"  {label} for {len(missing_files)} images...")
            for index, file in enumerate(missing_files):
                try:
                    meta = generator.analyze_image(
                        file,
                        location_hint=hint,
                        post_context=post_context,
                        image_index=index,
                        total_images=len(processed_files),
                        vision_hints=vision_hints_map.get(file, {}),
                    )
                    if meta and meta.get("success"):
                        analysis = dict(meta.get("analysis", {}))
                        analysis["_source"] = meta.get("source", label.lower())
                        if meta.get("tokens_used") is not None:
                            analysis["_tokens_used"] = meta.get("tokens_used")
                        metadata_dict[file] = analysis
                        added += 1
                    else:
                        self.log(f"    ⚠️  {Path(file).name}: {str(meta.get('error', 'unknown metadata error'))[:160]}")
                except Exception as e:
                    self.log(f"    ⚠️  {Path(file).name}: {str(e)[:160]}")
            return added

        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                added = fill_with_generator(
                    YOMetadataGenerator(api_key=api_key, use_gpt=True),
                    "🧠 GPT-4 Vision",
                )
                if added:
                    metadata_source = "gpt4_vision"
                    self.log(f"  ✓ GPT-4 Vision: {added} images analyzed")
        except Exception as e:
            self.log(f"  ⚠️  GPT-4 Vision error: {str(e)[:80]}")

        if len(metadata_dict) < len(processed_files):
            try:
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if api_key:
                    added = fill_with_generator(
                        YOMetadataGenerator(api_key=api_key, use_gpt=False),
                        "📜 Claude Vision",
                    )
                    if added:
                        metadata_source = "claude_vision" if metadata_source == "fallback" else "hybrid_all"
                        self.log(f"  ✓ Claude Vision: {added} images analyzed")
            except Exception as e:
                self.log(f"  ⚠️  Claude Vision error: {str(e)[:80]}")

        # Fallback for remaining missing images
        if len(metadata_dict) < len(processed_files):
            missing = [f for f in processed_files if f not in metadata_dict]
            self.log(f"  📄 Generating title-focused fallback metadata for {len(missing)} images...")

            for file in missing:
                fallback_meta = build_basic_metadata(
                    image_path=file,
                    location_hint=hint,
                    post_context=post_context,
                )
                fallback_meta["_source"] = "fallback"
                metadata_dict[file] = fallback_meta

            if missing:
                metadata_source = "hybrid" if metadata_source != "fallback" else "fallback"

        # Step 3b: Finalize filename and embed metadata
        self.log(f"\n🏷️  STEP 3b: Finalize filenames and embed metadata")
        used_slugs: set[str] = set()
        finalized_files: list[str] = []
        finalized_metadata: dict[str, Dict] = {}
        finalized_details: dict[str, Dict] = {}
        for file in processed_files:
            meta = metadata_dict.get(file, {})
            process_info = processed_details.get(file, {})
            vision_hints = vision_hints_map.get(file)
            if vision_hints:
                meta["_vision_hints"] = vision_hints
            slug_source_path = str(process_info.get("input") or file)

            # Enrich with Visual Memory DB metadata when the source is a Mac Photos
            # UUID path whose EXIF is empty — DB holds city/location/scene directly.
            if not isinstance(meta.get("_source_embedded"), dict) or not meta.get("_source_embedded"):
                vm_record = query_asset_from_visual_memory(get_visual_memory_db_path(), slug_source_path)
                if vm_record:
                    city = (vm_record.get("city") or "").strip()
                    location = (vm_record.get("location") or "").strip()
                    scene = (vm_record.get("scene") or "").strip()
                    activity = (vm_record.get("activity") or "").strip()
                    place = city or location
                    desc_parts = [p for p in [place] if p]
                    if scene and scene not in ("general",):
                        desc_parts.append(scene)
                    if activity and activity not in ("general", "walking"):
                        desc_parts.append(activity)
                    if desc_parts:
                        meta["_source_embedded"] = {
                            "description": " ".join(desc_parts),
                            "location": place,
                            "title": "",
                            "keywords": [],
                        }

            slug_candidates = build_publish_slug_candidates(meta, post_context, slug_source_path)
            candidate_slug = ensure_unique_slug(slug_candidates[0], used_slugs)
            for slug in slug_candidates:
                trial = ensure_unique_slug(slug, used_slugs)
                if trial == slug:
                    candidate_slug = trial
                    break
            used_slugs.add(candidate_slug)
            final_path = ensure_publish_path(self.work_dir, candidate_slug)
            source_path = Path(file)
            if source_path != final_path:
                source_path.replace(final_path)
            embedded = embed_metadata(str(final_path), meta)
            meta["embedded"] = embedded
            meta["final_slug"] = final_path.stem
            finalized_files.append(str(final_path))
            finalized_metadata[str(final_path)] = meta
            finalized_details[str(final_path)] = process_info
            self.log(f"  ✓ {source_path.name} -> {final_path.name}" + (" + embedded" if embedded else ""))

        processed_files = finalized_files
        metadata_dict = finalized_metadata
        processed_details = finalized_details

        # Step 3c: quality gate
        self.log(f"\n🛡️  STEP 3c: Validate crop, filter, metadata")
        allow_fallback_upload = os.getenv("YO_ALLOW_FALLBACK_UPLOAD", "0").strip().lower() in {"1", "true", "yes", "on"}
        title_counts: dict[str, int] = defaultdict(int)
        for meta in metadata_dict.values():
            title_counts[normalize_text(meta.get("title", ""))] += 1

        approved_files: list[str] = []
        approved_metadata: dict[str, Dict] = {}
        approved_details: dict[str, Dict] = {}
        blocked_assets: list[Dict] = []
        for file in processed_files:
            meta = metadata_dict[file]
            process_info = processed_details.get(file)
            duplicate_title = title_counts[normalize_text(meta.get("title", ""))] > 1
            errors = validate_metadata(meta, post_context, duplicate_title=duplicate_title)
            errors.extend(validate_processed_asset(meta, process_info))
            if errors:
                if allow_fallback_upload:
                    # Server ops mode: keep pipeline moving even when semantic validators are unavailable.
                    meta.setdefault("quality_gate_warnings", errors)
                    approved_files.append(file)
                    approved_metadata[file] = meta
                    approved_details[file] = process_info or {}
                    self.log(f"  ⚠ Approved with warnings {Path(file).name}: {'; '.join(errors)}")
                    continue
                blocked_assets.append({"file": Path(file).name, "errors": errors})
                self.log(f"  ✗ Blocked {Path(file).name}: {'; '.join(errors)}")
                continue
            approved_files.append(file)
            approved_metadata[file] = meta
            approved_details[file] = process_info or {}
            self.log(f"  ✓ Approved {Path(file).name}")

        processed_files = approved_files
        metadata_dict = approved_metadata
        processed_details = approved_details
        result["steps"]["quality_gate"] = {
            "approved": len(processed_files),
            "blocked": blocked_assets,
        }

        result["steps"]["metadata_generated"] = {
            "count": len(metadata_dict),
            "source": metadata_source,
        }
        self.log(f"  ✓ Metadata ready ({metadata_source})")

        # If caller specified an explicit heading, force it on every image.
        if heading:
            for key in metadata_dict:
                metadata_dict[key]["heading"] = heading
                if heading_level:
                    metadata_dict[key]["heading_level"] = heading_level
            self.log(f"  📌 Heading override: H{heading_level or '?'} → {heading!r}")

        # Step 4: Upload veya yerel çıktı
        if not upload_mode:
            # Post ID yok → işlenmiş dosyaları VIL dir'e taşı
            vil_dir = get_vil_dir()
            vil_dir.mkdir(parents=True, exist_ok=True)
            self.log(f"\n💾 STEP 4: Yerel çıktı → {vil_dir}")
            moved: list[str] = []
            for f in processed_files:
                dest = vil_dir / Path(f).name
                Path(f).replace(dest)
                moved.append(str(dest))
                self.log(f"  ✓ {Path(f).name} → {vil_dir.name}/")
            result["status"] = "local"
            result["uploaded_count"] = 0
            result["local_files"] = moved
        else:
            self.log(f"\n📤 STEP 4: Upload to WordPress ({site})")
            try:
                if not processed_files:
                    self.log(f"  ✗ No normal images to upload")
                    result["status"] = "skipped"
                    result["uploaded_count"] = 0
                    result["panoramic_count"] = len(panoramic_images)
                else:
                    upload_result = upload_images_batch(
                        image_files=processed_files,
                        metadata_dict=metadata_dict,
                        post_id=post_id,
                        site=site,
                    )
                    result["steps"]["upload_complete"] = upload_result
                    result["status"] = "success"
                    result["uploaded_count"] = len(upload_result["uploaded"])
                    result["failed_count"] = len(upload_result["failed"])
                    self.log(f"\n  ✓ Uploaded: {len(upload_result['uploaded'])} images")
                    if upload_result["failed"]:
                        self.log(f"  ⚠️  Failed: {len(upload_result['failed'])} images")
                    if panoramic_images:
                        self.log(f"  ℹ️  Panoramik resimleri pillar pages'e manuel kopyala")
            except Exception as e:
                self.log(f"  ✗ Upload error: {e}")
                result["status"] = "failed"
                result["error"] = str(e)

        # Final summary
        self.log(f"\n{'='*60}")
        self.log(f"✅ Pipeline complete!")
        self.log(f"  Status: {result['status']}")
        self.log(f"  Uploaded: {result.get('uploaded_count', 0)}")
        self.log(f"  Failed: {result.get('failed_count', 0)}")
        self.log(f"{'='*60}")

        # Save log
        with open(self.log_file, "w") as f:
            json.dump(result, f, indent=2)
        self.log(f"\n📝 Log saved: {self.log_file}")

        return result


def main():
    """CLI entry point"""
    import sys

    if len(sys.argv) < 2:
        print("Kullanım:")
        print("  VIL:       '<N> foto yo <post_id> [GE|GD]'")
        print("  Unsplash:  'unsplash:<sorgu> <N> foto yo <post_id>'")
        print("  İsim:      '<isim> yo <post_id>'")
        print("  Semantic upload:  '<lokasyon> <N> foto [filtre] yo <post_id>'")
        print("  Semantic yerel:   '<lokasyon> <N> foto [filtre]'")
        print("  Post bağlamı:     'Post: <post_id> <sorgu> <N> foto'")
        print()
        print("Örnekler:")
        print("  python3 yo_orchestrator.py '5 foto yo 21312'")
        print("  python3 yo_orchestrator.py 'madura adası 5 foto insan yo 21312'")
        print("  python3 yo_orchestrator.py 'alaçatı 3 foto sokak'")
        print("  python3 yo_orchestrator.py 'Post: 1009 içinde insan olan 5 foto'")
        print()
        print("Filtreler: insan, sokak, mimari, doga, deniz, gece, pazar, tapinak, tekne")
        sys.exit(1)

    command = sys.argv[1]

    # Parse command
    params = YOCommandParser.parse(command)
    if not params:
        print(f"✗ Invalid command: {command}")
        print(f"  Expected: '<count> foto yo <post_id> [site]'")
        sys.exit(1)

    print(f"✓ Parsed: {params}")

    # Run pipeline
    orchestrator = YOOrchestrator()
    result = orchestrator.run_pipeline(**params)

    # Exit code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
