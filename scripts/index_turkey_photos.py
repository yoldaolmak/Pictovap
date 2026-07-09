#!/usr/bin/env python3.11
"""Pictova — Global photos & video indeksleyici (Mac Photos).

Hierarchy: Continent → Country → City (Meridyen harita yapısı ile uyumlu)

Filtre:
  DAHIL : Tüm GPS'li ve GPS'siz photos ve videolar
  Kişisel: Aile albümleri ve aile fertlerinin olduğu photoslar
           is_personal=1 saved as (no AI scan, stays in DB)
  Değerli: Sadece Kemal Kaya olan photoslar is_personal=0 (full AI scan)
  Video : is_video=1 olarak kaydedilir (AI taranmaz, on-demand analiz)

Output: updates visual_memory.db (upsert).
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

# Family/personal albums — no longer skipped, is_personal=1 olarak kaydediliyor
PERSONAL_ALBUMS = {
    "Ayşa", "Ella", "Kemal", "Pamuk", "Kıymet",
    "Gömbe 🏡", "Home",
}

# Social media / import albums — completely skipped (düşük kalite)
SKIP_ALBUMS = {
    "Instagram", "Twitter", "WhatsApp", "InShot", "Import",
}

# Family members — excluding Kemal, others are personal filter
OWNER_NAME = "Kemal"  # Photo owner — only valuable if he is the only one
FAMILY_PERSONS = {"Ayşe", "Ayşa", "Ella", "Luka", "Pamuk", "Kıymet"}

# Izmir home city — not travel content, but still index (is_personal=1)
HOME_CITIES = {
    "Karsiyaka", "Karşıyaka", "Menemen", "Balcova", "Balçova",
    "Cigli", "Çiğli", "Yesilyurt", "Yeşilyurt", "Buca",
    "Gaziemir", "Konak", "Bornova", "Karsiyaka", "Narlidere",
    "Narlıdere", "Bayrakli", "Bayraklı", "Kınık", "Aliağa",
}

# ── Coğrafi Hiyerarşi: Kıta Haritası (ISO 3166-1 alpha-2 → Kıta) ───────────
CONTINENT_MAP = {
    # Avrupa
    "AL": "Avrupa", "AD": "Avrupa", "AT": "Avrupa", "BY": "Avrupa",
    "BE": "Avrupa", "BA": "Avrupa", "BG": "Avrupa", "HR": "Avrupa",
    "CY": "Avrupa", "CZ": "Avrupa", "DK": "Avrupa", "EE": "Avrupa",
    "FI": "Avrupa", "FR": "Avrupa", "DE": "Avrupa", "GR": "Avrupa",
    "HU": "Avrupa", "IS": "Avrupa", "IE": "Avrupa", "IT": "Avrupa",
    "XK": "Avrupa", "LV": "Avrupa", "LI": "Avrupa", "LT": "Avrupa",
    "LU": "Avrupa", "MT": "Avrupa", "MD": "Avrupa", "MC": "Avrupa",
    "ME": "Avrupa", "NL": "Avrupa", "MK": "Avrupa", "NO": "Avrupa",
    "PL": "Avrupa", "PT": "Avrupa", "RO": "Avrupa", "RU": "Avrupa",
    "SM": "Avrupa", "RS": "Avrupa", "SK": "Avrupa", "SI": "Avrupa",
    "ES": "Avrupa", "SE": "Avrupa", "CH": "Avrupa", "UA": "Avrupa",
    "GB": "Avrupa", "VA": "Avrupa",
    # Asya
    "AF": "Asya", "AM": "Asya", "AZ": "Asya", "BH": "Asya",
    "BD": "Asya", "BT": "Asya", "BN": "Asya", "KH": "Asya",
    "CN": "Asya", "GE": "Asya", "IN": "Asya", "ID": "Asya",
    "IR": "Asya", "IQ": "Asya", "IL": "Asya", "JP": "Asya",
    "JO": "Asya", "KZ": "Asya", "KW": "Asya", "KG": "Asya",
    "LA": "Asya", "LB": "Asya", "MY": "Asya", "MV": "Asya",
    "MN": "Asya", "MM": "Asya", "NP": "Asya", "KP": "Asya",
    "OM": "Asya", "PK": "Asya", "PS": "Asya", "PH": "Asya",
    "QA": "Asya", "SA": "Asya", "SG": "Asya", "KR": "Asya",
    "LK": "Asya", "SY": "Asya", "TW": "Asya", "TJ": "Asya",
    "TH": "Asya", "TL": "Asya", "TR": "Asya", "TM": "Asya",
    "AE": "Asya", "UZ": "Asya", "VN": "Asya", "YE": "Asya",
    # Afrika
    "DZ": "Afrika", "AO": "Afrika", "BJ": "Afrika", "BW": "Afrika",
    "BF": "Afrika", "BI": "Afrika", "CV": "Afrika", "CM": "Afrika",
    "CF": "Afrika", "TD": "Afrika", "KM": "Afrika", "CD": "Afrika",
    "CG": "Afrika", "CI": "Afrika", "DJ": "Afrika", "EG": "Afrika",
    "GQ": "Afrika", "ER": "Afrika", "SZ": "Afrika", "ET": "Afrika",
    "GA": "Afrika", "GM": "Afrika", "GH": "Afrika", "GN": "Afrika",
    "GW": "Afrika", "KE": "Afrika", "LS": "Afrika", "LR": "Afrika",
    "LY": "Afrika", "MG": "Afrika", "MW": "Afrika", "ML": "Afrika",
    "MR": "Afrika", "MU": "Afrika", "MA": "Afrika", "MZ": "Afrika",
    "NA": "Afrika", "NE": "Afrika", "NG": "Afrika", "RW": "Afrika",
    "SN": "Afrika", "SC": "Afrika", "SL": "Afrika", "SO": "Afrika",
    "ZA": "Afrika", "SS": "Afrika", "SD": "Afrika", "TZ": "Afrika",
    "TG": "Afrika", "TN": "Afrika", "UG": "Afrika", "ZM": "Afrika",
    "ZW": "Afrika",
    # Kuzey Amerika
    "AG": "Kuzey Amerika", "BS": "Kuzey Amerika", "BB": "Kuzey Amerika",
    "BZ": "Kuzey Amerika", "CA": "Kuzey Amerika", "CR": "Kuzey Amerika",
    "CU": "Kuzey Amerika", "DM": "Kuzey Amerika", "DO": "Kuzey Amerika",
    "SV": "Kuzey Amerika", "GD": "Kuzey Amerika", "GT": "Kuzey Amerika",
    "HT": "Kuzey Amerika", "HN": "Kuzey Amerika", "JM": "Kuzey Amerika",
    "MX": "Kuzey Amerika", "NI": "Kuzey Amerika", "PA": "Kuzey Amerika",
    "KN": "Kuzey Amerika", "LC": "Kuzey Amerika", "VC": "Kuzey Amerika",
    "TT": "Kuzey Amerika", "US": "Kuzey Amerika",
    # Güney Amerika
    "AR": "Güney Amerika", "BO": "Güney Amerika", "BR": "Güney Amerika",
    "CL": "Güney Amerika", "CO": "Güney Amerika", "EC": "Güney Amerika",
    "GY": "Güney Amerika", "PY": "Güney Amerika", "PE": "Güney Amerika",
    "SR": "Güney Amerika", "UY": "Güney Amerika", "VE": "Güney Amerika",
    # Okyanusya
    "AU": "Okyanusya", "FJ": "Okyanusya", "KI": "Okyanusya",
    "MH": "Okyanusya", "FM": "Okyanusya", "NR": "Okyanusya",
    "NZ": "Okyanusya", "PW": "Okyanusya", "PG": "Okyanusya",
    "WS": "Okyanusya", "SB": "Okyanusya", "TO": "Okyanusya",
    "TV": "Okyanusya", "VU": "Okyanusya",
}


def _country_code_to_continent(code: str) -> str:
    """ISO ülke kodunu kıta adına çevir."""
    return CONTINENT_MAP.get(code.upper(), "Diğer")


DB_PATH = Path(os.environ.get(
    "YO_VISUAL_MEMORY_DB",
    "/Users/yoldaolmak/Projects/Pictova/data/visual_memory.db",
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
    country_code TEXT NOT NULL DEFAULT '',
    continent TEXT NOT NULL DEFAULT '',
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
    story_score REAL NOT NULL DEFAULT 0,
    orientation TEXT NOT NULL DEFAULT '',
    capture_context TEXT NOT NULL DEFAULT '',
    selection_score REAL NOT NULL DEFAULT 0,
    is_personal INTEGER NOT NULL DEFAULT 0,
    personal_reason TEXT NOT NULL DEFAULT '',
    is_video INTEGER NOT NULL DEFAULT 0,
    video_duration REAL,
    vision_scan_status TEXT NOT NULL DEFAULT 'pending',
    vision_last_scanned_at TEXT,
    vision_last_error TEXT,
    scene_ml TEXT,
    time_of_day TEXT,
    metadata_keywords_json TEXT NOT NULL DEFAULT '[]',
    exif_metadata_json TEXT NOT NULL DEFAULT '{}',
    raw_metadata_json TEXT NOT NULL DEFAULT '{}',
    apple_labels_json TEXT NOT NULL DEFAULT '[]'
);
"""

MIGRATE_COLUMNS = [
    "ALTER TABLE asset_index ADD COLUMN story_score REAL NOT NULL DEFAULT 0",
    "ALTER TABLE asset_index ADD COLUMN is_video INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE asset_index ADD COLUMN video_duration REAL",
    "ALTER TABLE asset_index ADD COLUMN state_province TEXT",
    "ALTER TABLE asset_index ADD COLUMN sub_admin_area TEXT",
    "ALTER TABLE asset_index ADD COLUMN country_code TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE asset_index ADD COLUMN continent TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE asset_index ADD COLUMN apple_labels_json TEXT NOT NULL DEFAULT '[]'",
]

UPSERT_SQL = """
INSERT INTO asset_index (
    source_id, source_type, source_path, folder_path, filename, file_extension,
    checksum,
    width, height, created_at, camera_make, camera_model,
    city, country, country_code, continent, latitude, longitude,
    album_names_json, title, description,
    orientation, vision_scan_status,
    metadata_keywords_json, quality_score,
    summary, scene, location, activity,
    objects_json, ai_keywords_json, places_json, people_json, story_tags_json,
    capture_context, exif_metadata_json, raw_metadata_json,
    state_province, sub_admin_area,
    is_personal, personal_reason, is_video, video_duration, apple_labels_json
) VALUES (
    :source_id, 'mac_photos', :source_path, :folder_path, :filename, :file_extension,
    '',
    :width, :height, :created_at, :camera_make, :camera_model,
    :city, :country, :country_code, :continent, :latitude, :longitude,
    :album_names_json, :title, :description,
    :orientation, :vision_scan_status,
    :metadata_keywords_json, :quality_score,
    '', '', :location, '',
    '[]', '[]', '[]', :people_json, '[]',
    '', '{}', '{}',
    :state_province, :sub_admin,
    :is_personal, :personal_reason, :is_video, :video_duration, :apple_labels_json
)
ON CONFLICT(source_id) DO UPDATE SET
    source_path = excluded.source_path,
    city = excluded.city,
    country = excluded.country,
    country_code = excluded.country_code,
    continent = excluded.continent,
    latitude = excluded.latitude,
    longitude = excluded.longitude,
    album_names_json = excluded.album_names_json,
    people_json = excluded.people_json,
    width = excluded.width,
    height = excluded.height,
    quality_score = excluded.quality_score,
    orientation = excluded.orientation,
    metadata_keywords_json = excluded.metadata_keywords_json,
    state_province = excluded.state_province,
    sub_admin_area = excluded.sub_admin_area,
    is_personal = excluded.is_personal,
    personal_reason = excluded.personal_reason,
    is_video = excluded.is_video,
    video_duration = excluded.video_duration,
    apple_labels_json = excluded.apple_labels_json;
"""


# ── Filtre ────────────────────────────────────────────────────────────────────

def _classify_photo(photo: osxphotos.PhotoInfo) -> tuple[str, int, str]:
    """Fotoğrafı sınıflandır.

    Returns:
        (action, is_personal, personal_reason)
        action: 'include' | 'skip'
    """
    place = photo.place
    
    # Sosyal medya / import albümleri — tamamen atla (düşük kalite)
    photo_albums = {a.title for a in (photo.album_info or [])}
    bad_social = photo_albums & SKIP_ALBUMS
    if bad_social:
        return "skip", 0, f"social_album={bad_social}"

    is_personal = 0
    personal_reason = ""

    # Personal album check — atlamak yerine is_personal=1 olarak işaretle
    personal_albums = photo_albums & PERSONAL_ALBUMS
    if personal_albums:
        is_personal = 1
        personal_reason = f"album={personal_albums}"

    # Kişi analizi — akıllı filtreleme
    try:
        persons = {pp.name for pp in (photo.person_info or []) if pp.name}
        family_in_photo = persons & FAMILY_PERSONS
        owner_in_photo = any(OWNER_NAME.lower() in p.lower() for p in persons)

        if family_in_photo:
            if owner_in_photo and not family_in_photo:
                # Sadece Kemal → değerli, is_personal=0
                pass
            else:
                # Aile fertleri var → kişisel
                is_personal = 1
                personal_reason = personal_reason or f"family={family_in_photo}"
    except Exception:
        pass

    # İzmir ev şehri — kişisel olarak işaretle ama atla değil
    city_names = getattr(getattr(place, "names", None), "city", None) or []
    city = city_names[0] if city_names else ""
    if city in HOME_CITIES and not is_personal:
        is_personal = 1
        personal_reason = personal_reason or f"home_city={city}"

    return "include", is_personal, personal_reason


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
    print(f"📸 Photos Library yükleniyor (photos + video)...")
    db_photos = osxphotos.PhotosDB()
    all_photos = db_photos.photos(movies=False)
    all_videos = db_photos.photos(movies=True, images=False)
    all_items = all_photos + all_videos
    print(f"   Total: {len(all_photos):,} photos + {len(all_videos):,} video = {len(all_items):,}")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.execute(CREATE_SQL)
    # Migrate columns for existing DBs
    for mig_sql in MIGRATE_COLUMNS:
        try:
            con.execute(mig_sql)
        except sqlite3.OperationalError:
            pass  # already exists
    con.commit()

    included = skipped = errors = 0
    personal_count = video_count = 0
    skip_reasons: dict[str, int] = {}

    print(f"\n🔍 Tüm arşiv taranyyor (Kıta → Ülke → Şehir)...")
    for i, photo in enumerate(all_items):
        is_video = 1 if photo.ismovie else 0

        try:
            action, is_personal, personal_reason = _classify_photo(photo)
        except Exception as exc:
            errors += 1
            continue

        if action.startswith("skip"):
            skipped += 1
            reason_key = personal_reason.split("=")[0] if personal_reason else action
            skip_reasons[reason_key] = skip_reasons.get(reason_key, 0) + 1
            continue

        if is_personal:
            personal_count += 1
        if is_video:
            video_count += 1

        path = photo.path or ""
        # iCloud photoslar path=None olabilir — metadata yine de indeksle
        is_icloud = 1 if not path else 0

        p = Path(path)
        place = photo.place
        pnames = getattr(place, "names", None)
        country_names = getattr(pnames, "country", None) or []
        country = country_names[0] if country_names else None
        cc = (getattr(place, "country_code", None) or "").upper() if place else ""
        continent = _country_code_to_continent(cc) if cc else ""
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

        location_str = city or state_province or country or ""

        # Video ise AI taranmaz, photos ise kişisel değilse taranır
        if is_video:
            scan_status = "skipped_video"
        elif is_personal:
            scan_status = "skipped_personal"
        else:
            scan_status = "pending"

        # Video süresi
        video_duration = None
        if is_video:
            try:
                video_duration = photo.duration
            except Exception:
                pass

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
            "country_code": cc,
            "continent": continent,
            "latitude": lat,
            "longitude": lon,
            "album_names_json": json.dumps(albums, ensure_ascii=False),
            "title": photo.title,
            "description": photo.description,
            "orientation": "landscape" if (photo.width or 0) >= (photo.height or 1) else "portrait",
            "metadata_keywords_json": json.dumps(keywords, ensure_ascii=False),
            "people_json": json.dumps(persons, ensure_ascii=False),
            "quality_score": _quality(photo),
            "location": location_str,
            "state_province": state_province,
            "sub_admin": sub_admin,
            "is_icloud": is_icloud,
            "is_personal": is_personal,
            "personal_reason": personal_reason,
            "is_video": is_video,
            "video_duration": video_duration,
            "vision_scan_status": scan_status,
            "apple_labels_json": json.dumps(getattr(photo, "labels", None) or [], ensure_ascii=False),
        }
        try:
            con.execute(UPSERT_SQL, row)
            included += 1
        except Exception as exc:
            errors += 1
            print(f"  ✗ {p.name}: {exc}", file=sys.stderr)

        if (i + 1) % 500 == 0:
            con.commit()
            print(f"   {i+1:,}/{len(all_items):,} processed — {included} dahil ({personal_count} kişisel, {video_count} video), {skipped} skipped")

    con.commit()
    con.close()

    print(f"\n✅ Tamamlandı")
    print(f"   Dahil      : {included:,}")
    print(f"     Kişisel  : {personal_count:,} (is_personal=1, AI taranmaz)")
    print(f"     Video    : {video_count:,} (is_video=1, on-demand analiz)")
    print(f"     AI Scan  : {included - personal_count - video_count:,} (tam tarama yapılacak)")
    print(f"   Atlandı    : {skipped:,}")
    print(f"   Hata       : {errors:,}")
    print(f"   Atlanma nedenleri: {skip_reasons}")
    print(f"   DB         : {DB_PATH}")


if __name__ == "__main__":
    main()
