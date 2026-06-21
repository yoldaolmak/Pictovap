#!/usr/bin/env python3.11
"""Pictova — Türkiye fotoğraf indeksleyici.

Filtre:
  DAHIL : GPS ülke = Turkey, albümsüz veya seyahat albümü
  HARIÇ : kişisel/sosyal albümler, Kemal Kaya yüz etiketi

Çıktı: visual_memory.db günceller (upsert).
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import osxphotos

# ── Sabitler ─────────────────────────────────────────────────────────────────

EXCLUDE_ALBUMS = {
    "Ayşa", "Ella", "Kemal", "Pamuk", "Kıymet",
    "Gömbe 🏡", "Home",
    "Instagram", "Twitter", "WhatsApp", "InShot", "Import",
}

EXCLUDE_PERSONS: set[str] = set()  # albüm filtresi yeterli

# İzmir ev şehri — seyahat içeriği değil
EXCLUDE_CITIES = {
    "Karsiyaka", "Karşıyaka", "Menemen", "Balcova", "Balçova",
    "Cigli", "Çiğli", "Yesilyurt", "Yeşilyurt", "Buca",
    "Gaziemir", "Konak", "Bornova", "Karsiyaka", "Narlidere",
    "Narlıdere", "Bayrakli", "Bayraklı", "Kınık", "Aliağa",
}

DB_PATH = Path(os.environ.get(
    "YO_VISUAL_MEMORY_DB",
    "/Users/yoldaolmak/Downloads/YO_OS_VIL/data/visual_memory.db",
))

# ── DB init ───────────────────────────────────────────────────────────────────

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS asset_index (
    source_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL DEFAULT 'mac_photos',
    source_path TEXT NOT NULL,
    folder_path TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_extension TEXT NOT NULL,
    checksum TEXT NOT NULL DEFAULT '',
    width INTEGER,
    height INTEGER,
    created_at TEXT,
    camera_make TEXT,
    camera_model TEXT,
    city TEXT,
    country TEXT,
    latitude REAL,
    longitude REAL,
    album_names_json TEXT NOT NULL DEFAULT '[]',
    title TEXT,
    description TEXT,
    summary TEXT NOT NULL DEFAULT '',
    scene TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    activity TEXT NOT NULL DEFAULT '',
    objects_json TEXT NOT NULL DEFAULT '[]',
    ai_keywords_json TEXT NOT NULL DEFAULT '[]',
    places_json TEXT NOT NULL DEFAULT '[]',
    people_json TEXT NOT NULL DEFAULT '[]',
    story_tags_json TEXT NOT NULL DEFAULT '[]',
    quality_score REAL NOT NULL DEFAULT 0,
    orientation TEXT NOT NULL DEFAULT '',
    capture_context TEXT NOT NULL DEFAULT '',
    selection_score REAL NOT NULL DEFAULT 0,
    is_personal INTEGER NOT NULL DEFAULT 0,
    personal_reason TEXT NOT NULL DEFAULT '',
    vision_scan_status TEXT NOT NULL DEFAULT 'pending',
    vision_last_scanned_at TEXT,
    vision_last_error TEXT,
    scene_ml TEXT,
    time_of_day TEXT,
    metadata_keywords_json TEXT NOT NULL DEFAULT '[]',
    exif_metadata_json TEXT NOT NULL DEFAULT '{}',
    raw_metadata_json TEXT NOT NULL DEFAULT '{}'
);
"""

UPSERT_SQL = """
INSERT INTO asset_index (
    source_id, source_type, source_path, folder_path, filename, file_extension,
    checksum,
    width, height, created_at, camera_make, camera_model,
    city, country, latitude, longitude,
    album_names_json, title, description,
    orientation, vision_scan_status,
    metadata_keywords_json, quality_score,
    summary, scene, location, activity,
    objects_json, ai_keywords_json, places_json, people_json, story_tags_json,
    capture_context, exif_metadata_json, raw_metadata_json,
    state_province, sub_admin_area
) VALUES (
    :source_id, 'mac_photos', :source_path, :folder_path, :filename, :file_extension,
    '',
    :width, :height, :created_at, :camera_make, :camera_model,
    :city, :country, :latitude, :longitude,
    :album_names_json, :title, :description,
    :orientation, 'pending',
    :metadata_keywords_json, :quality_score,
    '', '', :location, '',
    '[]', '[]', '[]', '[]', '[]',
    '', '{}', '{}',
    :state_province, :sub_admin
)
ON CONFLICT(source_id) DO UPDATE SET
    source_path = excluded.source_path,
    city = excluded.city,
    country = excluded.country,
    latitude = excluded.latitude,
    longitude = excluded.longitude,
    album_names_json = excluded.album_names_json,
    width = excluded.width,
    height = excluded.height,
    state_province = excluded.state_province,
    sub_admin_area = excluded.sub_admin_area;
"""


# ── Filtre ────────────────────────────────────────────────────────────────────

def _should_include(photo: osxphotos.PhotoInfo) -> tuple[bool, str]:
    """(include, reason)"""
    # Türkiye GPS kontrolü — PlaceInfo5 için country_code kullan
    place = photo.place
    if not place:
        return False, "country=None"
    country_code = getattr(place, "country_code", None) or ""
    if country_code.upper() != "TR":
        return False, f"country_code={country_code!r}"

    # Kişisel albüm kontrolü
    photo_albums = {a.title for a in (photo.album_info or [])}
    bad = photo_albums & EXCLUDE_ALBUMS
    if bad:
        return False, f"album={bad}"

    # İzmir ev şehri filtresi
    city_names = getattr(getattr(place, "names", None), "city", None) or []
    city = city_names[0] if city_names else ""
    if city in EXCLUDE_CITIES:
        return False, f"city={city}"

    # Yüz etiketi kontrolü — sadece Kemal Kaya albümünü de zaten üstte yakaladık
    # person_info bazen albüm adını yansıtır, sadece kesin etiket olanlara bak
    try:
        persons = {pp.name for pp in (photo.person_info or []) if pp.name}
        bad_p = persons & EXCLUDE_PERSONS
        if bad_p:
            return False, f"person={bad_p}"
    except Exception:
        pass  # person_info hatası → geç, albüm filtresi yeterli

    return True, "ok"


def _quality(photo: osxphotos.PhotoInfo) -> float:
    """Basit kalite skoru 0-1."""
    score = 0.5
    if photo.width and photo.height:
        mp = (photo.width * photo.height) / 1_000_000
        score += min(mp / 20, 0.3)
    if photo.exif_info and photo.exif_info.iso:
        iso = photo.exif_info.iso
        if iso and iso < 800:
            score += 0.1
        elif iso and iso > 3200:
            score -= 0.1
    if photo.favorite:
        score += 0.1
    return round(min(max(score, 0.0), 1.0), 3)


# ── Ana akış ──────────────────────────────────────────────────────────────────

def main():
    print(f"📸 Photos Library yükleniyor...")
    db_photos = osxphotos.PhotosDB()
    all_photos = db_photos.photos(movies=False)
    print(f"   Toplam: {len(all_photos):,} fotoğraf")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.execute(CREATE_SQL)
    con.commit()

    included = skipped = errors = 0
    skip_reasons: dict[str, int] = {}

    print(f"\n🔍 Türkiye filtresi uygulanıyor...")
    for i, photo in enumerate(all_photos):
        try:
            ok, reason = _should_include(photo)
        except Exception as exc:
            errors += 1
            continue

        if not ok:
            skipped += 1
            skip_reasons[reason.split("=")[0]] = skip_reasons.get(reason.split("=")[0], 0) + 1
            continue

        path = photo.path or ""
        # iCloud fotoğraflar path=None olabilir — metadata yine de indeksle
        is_icloud = 1 if not path else 0

        p = Path(path)
        place = photo.place
        pnames = getattr(place, "names", None)
        country_names = getattr(pnames, "country", None) or []
        country = country_names[0] if country_names else "Türkiye"
        city_names = getattr(pnames, "city", None) or []
        city = city_names[0] if city_names else None
        state_names = getattr(pnames, "state_province", None) or []
        state_province = state_names[0] if state_names else None
        sub_admin_names = getattr(pnames, "sub_administrative_area", None) or []
        sub_admin = sub_admin_names[0] if sub_admin_names else None
        lat = photo.latitude
        lon = photo.longitude

        exif = photo.exif_info
        camera_make = (exif.camera_make if exif else None)
        camera_model = (exif.camera_model if exif else None)

        keywords = photo.keywords or []
        albums = [a.title for a in (photo.album_info or [])]
        persons = [p_.name for p_ in (photo.person_info or []) if p_.name]

        location_str = city or country or ""

        row = {
            "source_id": photo.uuid,
            "source_path": path,
            "folder_path": str(p.parent),
            "filename": p.name,
            "file_extension": p.suffix.lower(),
            "width": photo.width,
            "height": photo.height,
            "created_at": photo.date.isoformat() if photo.date else None,
            "camera_make": camera_make,
            "camera_model": camera_model,
            "city": city,
            "country": country,
            "latitude": lat,
            "longitude": lon,
            "album_names_json": json.dumps(albums, ensure_ascii=False),
            "title": photo.title,
            "description": photo.description,
            "orientation": "landscape" if (photo.width or 0) >= (photo.height or 1) else "portrait",
            "metadata_keywords_json": json.dumps(keywords, ensure_ascii=False),
            "quality_score": _quality(photo),
            "location": location_str,
            "state_province": state_province,
            "sub_admin": sub_admin,
            "is_icloud": is_icloud,
        }
        try:
            con.execute(UPSERT_SQL, row)
            included += 1
        except Exception as exc:
            errors += 1
            print(f"  ✗ {p.name}: {exc}", file=sys.stderr)

        if (i + 1) % 500 == 0:
            con.commit()
            print(f"   {i+1:,}/{len(all_photos):,} işlendi — {included} dahil, {skipped} atlandı")

    con.commit()
    con.close()

    print(f"\n✅ Tamamlandı")
    print(f"   Dahil   : {included:,}")
    print(f"   Atlandı : {skipped:,}")
    print(f"   Hata    : {errors:,}")
    print(f"   Atlanma nedenleri: {skip_reasons}")
    print(f"   DB      : {DB_PATH}")


if __name__ == "__main__":
    main()
