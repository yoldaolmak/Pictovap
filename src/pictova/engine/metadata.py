"""Metadata generation — vision chain ile + DB cache."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pictova.core.metadata_generator import build_basic_metadata
from pictova.engine.vision_chain import analyze_image_vision_chain, has_any_vision_source


def _db_cached_metadata(image_path: str) -> Optional[Dict[str, Any]]:
    """Visual memory DB'de önceden taranmış metadata var mı? Varsa döner."""
    try:
        from pictova.config import get_visual_memory_db_path
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


def _is_turkish(text: str) -> bool:
    """Metnin Türkçe olup olmadığını hızlıca tahmin et."""
    tr_chars = set("çğıöşüÇĞİÖŞÜ")
    tr_words = {"ve", "bir", "bu", "da", "de", "ile", "için", "olan", "gibi", "ise"}
    if any(c in tr_chars for c in text):
        return True
    words = set(text.lower().split())
    return len(words & tr_words) >= 2


def _kemal_voice_caption(summary: str, scene: str, location: str, keywords: list) -> str:
    """Vision summary'sini Kemal Kaya üslubuyla caption'a dönüştür.

    Kural: Kısa, gözlem odaklı, BBC Travel tonu. "Bu fotoğrafta", "Görselde"
    gibi AI kalıpları yasak. Sanki sahneyi hatırlıyorsun gibi yaz.
    Eğer summary İngilizce ise lokasyon+sahne+keyword ile Türkçe üret.
    """
    import re
    if summary and len(summary) > 20:
        s = summary.strip()
        # AI kalıplarını temizle
        for pat in (
            r"^(Bu (fotoğrafta|görselde|resimde)|Fotoğrafta|Görselde|Resimde)[,\s]*",
            r"^(The (image|photo|picture) (shows|depicts|features|captures))[,\s]*",
            r"^(This (image|photo|picture) (shows|depicts|features|captures))[,\s]*",
        ):
            s = re.sub(pat, "", s, flags=re.IGNORECASE).strip()
        # Kalıp cümlenin ortasında da üretilebiliyor; yalnız prefix temizliği yeterli değil.
        s = re.sub(
            r"\b(?:bu\s+)?(?:fotoğrafta|görselde|resimde)\b[:,]?\s*",
            "",
            s,
            flags=re.IGNORECASE,
        )
        s = re.sub(r"\bçekilmiş\b", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s+", " ", s).replace(" ,", ",").strip(" ,")
        if s and s[0].islower():
            s = s[0].upper() + s[1:]
        if s and not s.endswith((".", "!", "?")):
            s += "."
        # Türkçe ise kullan; İngilizce ise aşağı düş
        if _is_turkish(s):
            return s[:180]

    # Summary yoksa veya İngilizce ise: Türkçe lokasyon tabanlı fallback
    _skip = {"general", "other", "unknown", "various", "misc"}
    scene_tr_map = {
        "coast": "kıyı", "mountain": "dağ", "city": "şehir", "village": "köy",
        "forest": "orman", "lake": "göl", "valley": "vadi", "beach": "plaj",
        "castle": "kale", "ruins": "harabe", "market": "çarşı", "nature": "doğa",
        "landscape": "manzara", "harbor": "liman", "port": "liman",
    }
    # Önemli keyword'leri Türkçeleştirmeye çalış, gerisi bırak
    kw_clean = [k for k in keywords[:4]
                if k.lower() not in _skip
                and k.lower() not in (location or "").lower()
                and k.lower() not in (scene or "").lower()]

    scene_tr = scene_tr_map.get(scene.lower(), "") if (scene and scene.lower() not in _skip) else ""
    
    if location and scene_tr:
        if kw_clean:
            caption = f"{location} yakınlarında, {', '.join(kw_clean[:2])} detayları içeren {scene_tr} manzarası."
        else:
            caption = f"{location} yakınlarındaki {scene_tr} manzarası."
    elif location:
        if kw_clean:
            caption = f"{location} manzarasında {', '.join(kw_clean[:2])} detayları."
        else:
            caption = f"{location} manzarası."
    elif scene_tr:
        if kw_clean:
            caption = f"{scene_tr.capitalize()} karesinde {', '.join(kw_clean[:2])} öne çıkıyor."
        else:
            caption = f"{scene_tr.capitalize()} manzarası."
    else:
        if kw_clean:
            caption = f"Seyahat karesi: {', '.join(kw_clean[:2])}."
        else:
            caption = "Seyahat karesi."

    if caption and not caption.endswith((".", "!", "?")):
        caption += "."
    return caption[:180]


def _enrich_from_cache(cached: Dict, post_context: Dict) -> Dict:
    """DB cache'inden tam metadata formatı oluştur."""
    kws = cached.get("keywords", [])
    summary = cached.get("summary", "")
    scene = cached.get("scene", "")
    activity = cached.get("activity", "")
    location = str(post_context.get("title") or "").strip()
    kw_str = ", ".join(kws[:5]) if kws else location

    # İngilizce sahne terimlerini Türkçeye çevir
    _scene_tr: dict[str, str] = {
        "coast": "kıyı", "coastal": "kıyı", "shore": "kıyı",
        "beach": "plaj", "bay": "koy", "harbor": "liman", "harbour": "liman",
        "port": "liman", "sea": "deniz", "ocean": "deniz",
        "island": "ada", "peninsula": "yarımada",
        "mountain": "dağ", "hill": "tepe", "cliff": "uçurum",
        "valley": "vadi", "plateau": "yayla", "cave": "mağara",
        "waterfall": "şelale", "lake": "göl", "river": "nehir",
        "forest": "orman", "nature": "doğa", "landscape": "manzara",
        "village": "köy", "town": "kasaba", "city": "şehir",
        "street": "sokak", "market": "çarşı", "square": "meydan",
        "castle": "kale", "fortress": "kale", "ruins": "harabe",
        "mosque": "cami", "church": "kilise", "temple": "tapınak",
        "bridge": "köprü", "lighthouse": "deniz feneri",
        "garden": "bahçe", "park": "park",
        "food": "yemek", "restaurant": "restoran",
        "sunset": "gün batımı", "sunrise": "gün doğumu", "night": "gece",
    }
    scene_tr = _scene_tr.get(scene.lower(), scene) if scene else ""

    # alt: ekran okuyucu için sade, tanımlayıcı
    # summary Türkçe ise doğrudan kullan; İngilizce ise lokasyon+sahne birleştir
    if summary and _is_turkish(summary):
        alt = summary
    elif scene_tr and location:
        alt = f"{location} {scene_tr}"
    elif location:
        alt = location
    else:
        alt = kw_str

    # title: SEO, lokasyon + sahne (Türkçe, generic scene kelimeleri atla)
    _skip_scenes = {"general", "other", "unknown", "various", "misc"}
    meaningful_scene = scene_tr if scene and scene.lower() not in _skip_scenes else ""
    if meaningful_scene and location:
        title = f"{location} — {meaningful_scene.title()}"
    elif location:
        title = location
    elif meaningful_scene:
        title = meaningful_scene.title()
    else:
        # İlk keyword'den üret
        title = kws[0].title() if kws else kw_str

    caption = _kemal_voice_caption(summary, scene, location, kws)

    # description: lokasyon + içerik bağlamı (Türkçe scene tercih et)
    activity_or_scene = _scene_tr.get(activity.lower(), activity) if activity else scene_tr
    desc_parts = [p for p in [location, activity_or_scene, kw_str] if p]
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
    assigned_headings: Dict[str, Dict[str, Any]] | None = None,
    post_context: Dict[str, Any] | None = None,
) -> Dict[str, Dict[str, Any]]:
    post_context = post_context or {}
    assigned_headings = assigned_headings or {}
    metadata_dict: Dict[str, Dict[str, Any]] = {}
    for image_file in image_files:
        h_info = assigned_headings.get(image_file, {})
        heading_text = str(h_info.get("text", "")).strip() or str(post_context.get("title", "")).strip()
        metadata = build_basic_metadata(
            image_path=image_file,
            location_hint=heading_text,
            post_context=post_context,
        )
        if h_info:
            metadata["heading"] = h_info.get("text")
            metadata["heading_level"] = h_info.get("level")
        metadata_dict[image_file] = metadata
    return metadata_dict


def build_native_metadata_map(
    image_files: List[str],
    *,
    assigned_headings: Dict[str, Dict[str, Any]] | None = None,
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
    assigned_headings = assigned_headings or {}
    metadata_dict = build_basic_metadata_map(
        image_files,
        assigned_headings=assigned_headings,
        post_context=post_context,
    )

    normalized_mode = str(mode or "auto").strip().lower()
    if normalized_mode == "basic":
        raise RuntimeError(
            "mode=basic reddedildi: Pictovap basic fallback kullanmaz. "
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
        h_info = assigned_headings.get(image_file, {})
        heading_text = str(h_info.get("text", "")).strip() or str(post_context.get("title", "")).strip()

        # 0. DB cache kontrolü
        cached = _db_cached_metadata(image_file)
        if cached:
            # location_hint olarak heading_text'i kullan
            # _enrich_from_cache içinde post_context kullanılıyor ama location orada post_context['title']'den çekiliyor.
            # _enrich_from_cache override yapmak için özel bir location geçemiyoruz, o yüzden post_context kopyasını değiştirelim
            ctx = dict(post_context)
            if heading_text:
                ctx["title"] = heading_text
            enriched = _enrich_from_cache(cached, ctx)
            if h_info:
                enriched["heading"] = h_info.get("text")
                enriched["heading_level"] = h_info.get("level")
                
            if "pictova_unsplash" in str(image_file):
                parts = Path(image_file).stem.split("-by-")
                publisher = parts[-1].replace("_", " ") if len(parts) > 1 else "Bilinmiyor"
                enriched["caption"] = f"{enriched.get('caption', '').strip()} (Görsel: Unsplash, {publisher})"
                
            metadata_dict[image_file] = enriched
            warnings.append(f"{Path(image_file).name}: OK (db_cache)")
            continue

        # 1-3. Vision chain
        try:
            analysis = analyze_image_vision_chain(
                image_file,
                location_hint=heading_text,
                post_context=post_context,
            )
            source = analysis.pop("source", "vision_chain")
            analysis["caption"] = _kemal_voice_caption(
                str(analysis.get("caption") or analysis.get("summary") or ""),
                str(analysis.get("scene") or ""),
                heading_text,
                list(analysis.get("keywords") or []),
            )
            if h_info:
                analysis["heading"] = h_info.get("text")
                analysis["heading_level"] = h_info.get("level")
                
            if "pictova_unsplash" in str(image_file):
                parts = Path(image_file).stem.split("-by-")
                publisher = parts[-1].replace("_", " ") if len(parts) > 1 else "Bilinmiyor"
                analysis["caption"] = f"{analysis.get('caption', '').strip()} (Görsel: Unsplash, {publisher})"
                
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
