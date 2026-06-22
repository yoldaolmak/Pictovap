"""Metadata generation — vision chain ile + DB cache."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.core.metadata_generator import build_basic_metadata
from src.pictova.engine.vision_chain import analyze_image_vision_chain, has_any_vision_source


def _db_cached_metadata(image_path: str) -> Optional[Dict[str, Any]]:
    """Visual memory DB'de önceden taranmış metadata var mı? Varsa döner."""
    try:
        from src.pictova.config import get_visual_memory_db_path
        db_path = str(get_visual_memory_db_path())
        con = sqlite3.connect(db_path)
        row = con.execute("""
            SELECT ai_keywords_json, scene, activity, summary
            FROM asset_index
            WHERE source_path = ? AND vision_scan_status = 'done'
            LIMIT 1
        """, [image_path]).fetchone()
        con.close()
        if not row:
            return None
        kws = json.loads(row[0] or "[]")
        if not kws:
            return None
        return {
            "keywords": kws,
            "scene": row[1] or "",
            "activity": row[2] or "",
            "summary": row[3] or "",
        }
    except Exception:
        return None


def _kemal_voice_caption(summary: str, scene: str, location: str, keywords: list) -> str:
    """Vision summary'sini Kemal Kaya üslubuyla caption'a dönüştür.

    Kural: Kısa, gözlem odaklı, BBC Travel tonu. "Bu fotoğrafta", "Görselde"
    gibi AI kalıpları yasak. Sanki sahneyi hatırlıyorsun gibi yaz.
    """
    if summary and len(summary) > 20:
        # AI summary'sini temizle — kalıp ifadeleri kaldır
        import re
        s = summary.strip()
        # Yaygın AI kalıpları
        for pat in (
            r"^(Bu (fotoğrafta|görselde|resimde)|Fotoğrafta|Görselde|Resimde)\s*",
            r"^(The (image|photo|picture) (shows|depicts|features))\s*",
        ):
            s = re.sub(pat, "", s, flags=re.IGNORECASE).strip()
        if s and s[0].islower():
            s = s[0].upper() + s[1:]
        if s and not s.endswith((".", "!", "?")):
            s += "."
        return s[:180]

    # Summary yoksa veya çok kısaysa keywords + scene + location'dan üret
    parts = []
    if location:
        parts.append(location)
    if scene and scene.lower() not in (location or "").lower():
        scene_tr = {
            "coast": "kıyı", "mountain": "dağ", "city": "şehir", "village": "köy",
            "forest": "orman", "lake": "göl", "valley": "vadi", "beach": "plaj",
            "castle": "kale", "ruins": "harabe", "market": "çarşı",
        }.get(scene.lower(), scene)
        parts.append(scene_tr)
    if keywords:
        kw_extra = [k for k in keywords[:3] if k.lower() not in " ".join(parts).lower()]
        if kw_extra:
            parts.append(", ".join(kw_extra))
    return (". ".join(parts) + ".").strip(".")[:180] or "Seyahat karesi."


def _enrich_from_cache(cached: Dict, post_context: Dict) -> Dict:
    """DB cache'inden tam metadata formatı oluştur."""
    kws = cached.get("keywords", [])
    summary = cached.get("summary", "")
    scene = cached.get("scene", "")
    activity = cached.get("activity", "")
    location = str(post_context.get("title") or "").strip()
    kw_str = ", ".join(kws[:5]) if kws else location

    # alt: ekran okuyucu için sade, tanımlayıcı
    alt = summary or (f"{scene} — {location}".strip(" —") if scene or location else kw_str)

    # title: SEO, lokasyon + sahne
    if scene and location:
        title = f"{location} — {scene.title()}"
    elif location:
        title = location
    else:
        title = scene.title() or kw_str

    caption = _kemal_voice_caption(summary, scene, location, kws)

    # description: lokasyon + içerik bağlamı
    desc_parts = [p for p in [location, activity or scene, kw_str] if p]
    description = ". ".join(dict.fromkeys(desc_parts))

    return {
        "alt": alt[:125],
        "title": title[:60],
        "caption": caption,
        "description": description[:300],
        "keywords": kws,
        "source": "db_cache",
    }


def build_basic_metadata_map(
    image_files: List[str],
    *,
    location_hint: str = "",
    post_context: Dict[str, Any] | None = None,
) -> Dict[str, Dict[str, Any]]:
    post_context = post_context or {}
    metadata_dict: Dict[str, Dict[str, Any]] = {}
    for image_file in image_files:
        metadata = build_basic_metadata(
            image_path=image_file,
            location_hint=location_hint,
            post_context=post_context,
        )
        metadata["heading"] = post_context.get("title", "") or Path(image_file).stem
        metadata["heading_level"] = 2
        metadata_dict[image_file] = metadata
    return metadata_dict


def build_native_metadata_map(
    image_files: List[str],
    *,
    location_hint: str = "",
    post_context: Dict[str, Any] | None = None,
    mode: str = "auto",
) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """Vision chain ile metadata üret. DB cache'i önce kontrol eder.

    Öncelik:
      0. DB cache (vision_scan_status='done' — anlık, ücretsiz)
      1. Gemini Flash (GEMINI_API_KEY)
      2. Codex CLI web login
      3. Claude CLI web login
    Basic fallback YOK — hiçbiri çalışmıyorsa RuntimeError.
    """
    post_context = post_context or {}
    metadata_dict = build_basic_metadata_map(
        image_files,
        location_hint=location_hint,
        post_context=post_context,
    )

    normalized_mode = str(mode or "auto").strip().lower()
    if normalized_mode == "basic":
        raise RuntimeError(
            "mode=basic reddedildi: Pictova basic fallback kullanmaz. "
            "GEMINI_API_KEY ekle veya codex/claude oturumu aç."
        )

    if normalized_mode not in {"auto", "vision"}:
        raise RuntimeError(f"Bilinmeyen metadata modu: {normalized_mode!r}")

    if not has_any_vision_source():
        raise RuntimeError(
            "Hiç vision kaynağı bulunamadı.\n"
            "Seçenekler:\n"
            "  1. GEMINI_API_KEY=... (.env'e ekle — Google AI Studio, ücretsiz)\n"
            "  2. codex login  (terminalde)\n"
            "  3. claude oturumu (zaten açık ise çalışır)"
        )

    warnings: List[str] = []
    for image_file in image_files:
        # 0. DB cache kontrolü
        cached = _db_cached_metadata(image_file)
        if cached:
            enriched = _enrich_from_cache(cached, post_context)
            enriched["heading"] = post_context.get("title", "") or Path(image_file).stem
            enriched["heading_level"] = 2
            metadata_dict[image_file] = enriched
            warnings.append(f"{Path(image_file).name}: OK (db_cache)")
            continue

        # 1-3. Vision chain
        try:
            analysis = analyze_image_vision_chain(
                image_file,
                location_hint=location_hint,
                post_context=post_context,
            )
            source = analysis.pop("source", "vision_chain")
            analysis["heading"] = post_context.get("title", "") or Path(image_file).stem
            analysis["heading_level"] = 2
            metadata_dict[image_file] = analysis
            warnings.append(f"{Path(image_file).name}: OK ({source})")
        except RuntimeError as exc:
            raise RuntimeError(
                f"Görsel analizi başarısız: {Path(image_file).name}\n{exc}"
            ) from exc

    return metadata_dict, warnings


__all__ = [
    "build_basic_metadata",
    "build_basic_metadata_map",
    "build_native_metadata_map",
]
