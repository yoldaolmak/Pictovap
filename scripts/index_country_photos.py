#!/usr/bin/env python3.11
"""Pictova — Ülke bazlı fotoğraf indeksleyici.

TR dışındaki ülkeler için. Kişisel albümleri hariç tutar.
Kullanım: python3.11 scripts/index_country_photos.py --country IT --limit 5000
"""
from __future__ import annotations

import argparse
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

DB_PATH = Path(os.environ.get(
    "YO_VISUAL_MEMORY_DB",
    "/Users/yoldaolmak/Downloads/YO_OS_VIL/data/visual_memory.db",
))

UPSERT_SQL = """
INSERT INTO asset_index (
    source_id, source_type, source_path, folder_path, filename, file_extension,
    checksum, width, height, created_at, camera_make, camera_model,
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
    '', :width, :height, :created_at, :camera_make, :camera_model,
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


def _quality(photo: osxphotos.PhotoInfo) -> float:
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--country", required=True, help="ISO country code, örn: IT, GR, HR")
    parser.add_argument("--limit", type=int, default=0, help="Maksimum fotoğraf sayısı")
    args = parser.parse_args()

    country_code = args.country.upper()
    print(f"📸 Photos Library yükleniyor (hedef: {country_code})...")
    db_photos = osxphotos.PhotosDB()
    all_photos = db_photos.photos(movies=False)
    print(f"   Toplam: {len(all_photos):,} fotoğraf")

    con = sqlite3.connect(str(DB_PATH))
    # asset_index tablosu zaten mevcut (index_turkey_photos.py tarafından oluşturuldu)

    included = skipped = errors = 0
    processed = 0

    print(f"\n🔍 {country_code} filtresi uygulanıyor...")
    for photo in all_photos:
        if args.limit and included >= args.limit:
            break

        try:
            place = photo.place
            if not place:
                skipped += 1
                continue

            pc = (getattr(place, "country_code", None) or "").upper()
            if pc != country_code:
                skipped += 1
                continue

            # Kişisel albüm kontrolü
            photo_albums = {a.title for a in (photo.album_info or [])}
            if photo_albums & EXCLUDE_ALBUMS:
                skipped += 1
                continue

        except Exception:
            errors += 1
            continue

        path = photo.path or ""
        p = Path(path) if path else Path("")
        pnames = getattr(place, "names", None)
        country_names = getattr(pnames, "country", None) or []
        country_str = country_names[0] if country_names else country_code
        city_names = getattr(pnames, "city", None) or []
        city = city_names[0] if city_names else None
        state_names = getattr(pnames, "state_province", None) or []
        state_province = state_names[0] if state_names else None
        sub_admin_names = getattr(pnames, "sub_administrative_area", None) or []
        sub_admin = sub_admin_names[0] if sub_admin_names else None

        exif = photo.exif_info
        keywords = photo.keywords or []
        albums = [a.title for a in (photo.album_info or [])]
        location_str = city or state_province or country_str or ""

        row = {
            "source_id": photo.uuid,
            "source_path": path,
            "folder_path": str(p.parent) if path else "",
            "filename": p.name if path else photo.uuid,
            "file_extension": p.suffix.lower() if path else "",
            "width": photo.width,
            "height": photo.height,
            "created_at": photo.date.isoformat() if photo.date else None,
            "camera_make": exif.camera_make if exif else None,
            "camera_model": exif.camera_model if exif else None,
            "city": city,
            "country": country_str,
            "latitude": photo.latitude,
            "longitude": photo.longitude,
            "album_names_json": json.dumps(albums, ensure_ascii=False),
            "title": photo.title,
            "description": photo.description,
            "orientation": "landscape" if (photo.width or 0) >= (photo.height or 1) else "portrait",
            "metadata_keywords_json": json.dumps(keywords, ensure_ascii=False),
            "quality_score": _quality(photo),
            "location": location_str,
            "state_province": state_province,
            "sub_admin": sub_admin,
        }
        try:
            con.execute(UPSERT_SQL, row)
            included += 1
        except Exception as exc:
            errors += 1
            print(f"  ✗ {p.name}: {exc}", file=sys.stderr)

        processed += 1
        if processed % 200 == 0:
            con.commit()
            print(f"   {processed:,} işlendi — {included} dahil, {skipped} atlandı")

    con.commit()
    con.close()

    print(f"\n✅ {country_code} indeksleme tamamlandı")
    print(f"   Dahil   : {included:,}")
    print(f"   Atlandı : {skipped:,}")
    print(f"   Hata    : {errors:,}")
    print(f"   DB      : {DB_PATH}")


if __name__ == "__main__":
    main()
