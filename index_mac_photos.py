#!/usr/bin/env python3
"""
YO OS — Mac Photos genel tarayıcı
Kullanım: python3 index_mac_photos.py "Kızkalesi Mersin" [--list] [--min-width 1200]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import unicodedata
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
import sys
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from visual_memory.analyzer import analyze_image
from visual_memory.config import VisualMemoryConfig
from visual_memory.db import VisualMemoryDatabase
from visual_memory.enrich import enrich_record
from visual_memory.sources import DiscoveredImage


PHOTOS_DB       = Path("~/Pictures/Photos Library.photoslibrary/database/Photos.sqlite").expanduser()
PHOTOS_ORIGINALS = Path("~/Pictures/Photos Library.photoslibrary/originals").expanduser()
DATA_DIR        = PROJECT_ROOT / "data"
OPS_DIR         = PROJECT_ROOT / "ops_logs"


# ── Yardımcılar ─────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Türkçe → ASCII, küçük harf, diacritic temizle"""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9 ]", " ", ascii_text).strip()


def _slug(text: str) -> str:
    return re.sub(r"\s+", "-", _normalize(text))


def _build_sql_query(keywords: list[str]) -> tuple[str, list[str]]:
    """Verilen anahtar kelimeleri moment başlığı, şehir, ülke, EXIF location'da ara"""
    conditions = []
    params: list[str] = []
    for kw in keywords:
        like = f"%{kw}%"
        conditions.append(
            "(m.ZTITLE LIKE ? OR m.ZLOCATIONNAMES LIKE ? "
            "OR aa.ZCITY LIKE ? OR aa.ZCOUNTRY LIKE ? "
            "OR aa.ZORIGINALFILENAME LIKE ?)"
        )
        params.extend([like, like, like, like, like])

    where = " OR ".join(conditions) if conditions else "1=1"
    sql = f"""
    SELECT
        a.ZUUID            AS asset_uuid,
        aa.ZORIGINALFILENAME AS original_filename,
        m.ZTITLE           AS moment_title,
        m.ZLOCATIONNAMES   AS moment_location,
        aa.ZCITY           AS city,
        aa.ZCOUNTRY        AS country,
        a.ZLATITUDE        AS latitude,
        a.ZLONGITUDE       AS longitude,
        a.ZCLOUDLOCALSTATE AS cloud_local_state,
        a.ZWIDTH           AS width,
        a.ZHEIGHT          AS height,
        a.ZDATECREATED     AS date_created
    FROM ZASSET a
    JOIN ZMOMENT m ON m.Z_PK = a.ZMOMENT
    LEFT JOIN ZADDITIONALASSETATTRIBUTES aa ON aa.Z_PK = a.ZADDITIONALATTRIBUTES
    WHERE ({where})
    ORDER BY a.ZDATECREATED;
    """
    return sql, params


def iter_originals(root: Path, extensions: tuple[str, ...]) -> dict[str, Path]:
    by_uuid: dict[str, Path] = {}
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if path.is_file() and path.suffix.lower() in extensions:
            by_uuid[path.stem.upper()] = path
    return by_uuid


def load_rows(keywords: list[str]) -> list[sqlite3.Row]:
    if not PHOTOS_DB.exists():
        print(f"⚠️  Photos Library bulunamadı: {PHOTOS_DB}")
        return []
    conn = sqlite3.connect(PHOTOS_DB)
    conn.row_factory = sqlite3.Row
    sql, params = _build_sql_query(keywords)
    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError as exc:
        # Bazı sütunlar (ZCITY, ZCOUNTRY) eski Photos versiyonlarında yok
        # Sadece moment başlığıyla fallback
        print(f"  ⚠️  Tam sorgu çalışmadı ({exc}), moment başlığıyla yeniden deneniyor…")
        conds = " OR ".join("m.ZTITLE LIKE ?" for _ in keywords)
        fallback_sql = f"""
        SELECT a.ZUUID AS asset_uuid, aa.ZORIGINALFILENAME AS original_filename,
               m.ZTITLE AS moment_title, NULL AS moment_location,
               NULL AS city, NULL AS country,
               a.ZLATITUDE AS latitude, a.ZLONGITUDE AS longitude,
               a.ZCLOUDLOCALSTATE AS cloud_local_state,
               a.ZWIDTH AS width, a.ZHEIGHT AS height, a.ZDATECREATED AS date_created
        FROM ZASSET a
        JOIN ZMOMENT m ON m.Z_PK = a.ZMOMENT
        LEFT JOIN ZADDITIONALASSETATTRIBUTES aa ON aa.Z_PK = a.ZADDITIONALATTRIBUTES
        WHERE {conds}
        ORDER BY a.ZDATECREATED;
        """
        rows = conn.execute(fallback_sql, [f"%{kw}%" for kw in keywords]).fetchall()
    finally:
        conn.close()
    return rows


def overlay_from_row(row: sqlite3.Row, location_label: str) -> dict:
    moment_title = (row["moment_title"] or "").strip()
    city = (row["city"] or "").strip()
    country = (row["country"] or "").strip()
    kws = [location_label.lower()]
    if moment_title:
        kws.append(moment_title.lower())
    if city:
        kws.append(city.lower())
    if country:
        kws.append(country.lower())
    return {
        "title": moment_title or location_label,
        "description": f"Fotoğraf: {moment_title or location_label}",
        "keywords": kws,
        "city": city or None,
        "country": country or None,
        "album_names": [moment_title] if moment_title else [],
        "favorite": False,
    }


# ── Ana İş ──────────────────────────────────────────────────────────────────

def run(location: str, min_width: int = 0, list_only: bool = False) -> None:
    keywords = location.split()
    slug = _slug(location)
    db_path = DATA_DIR / f"{slug}.sqlite"
    log_path = OPS_DIR / f"mac_photos_{slug}.log"

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OPS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n📷 Mac Photos taranıyor: '{location}'")
    print(f"   Anahtar kelimeler: {keywords}")

    rows = load_rows(keywords)
    print(f"   Bulunan satır: {len(rows)}")

    if not rows:
        print("   Sonuç bulunamadı.")
        return

    config = VisualMemoryConfig(database_path=db_path, scan_photos_library=False, external_roots=[])
    originals = iter_originals(PHOTOS_ORIGINALS, config.image_extensions)

    records = []
    enrichments = []
    missing = []
    skipped_size = 0
    moments: Counter[str] = Counter()

    for row in rows:
        uuid = row["asset_uuid"]
        if not uuid:
            continue

        # Boyut filtresi (Photos DB'den)
        w = row["width"] or 0
        if min_width and w < min_width:
            skipped_size += 1
            continue

        orig_path = originals.get(str(uuid).upper())
        if orig_path is None:
            missing.append({
                "uuid": uuid,
                "filename": row["original_filename"],
                "moment": row["moment_title"],
                "cloud_state": row["cloud_local_state"],
            })
            continue

        record = analyze_image(
            DiscoveredImage(path=orig_path, source_type="mac_photos"),
            photos_overlay=overlay_from_row(row, location),
        )
        enrichment = enrich_record(record)
        records.append(record)
        enrichments.append(enrichment)
        moments[(row["moment_title"] or "bilinmiyor").replace("\xa0", " ")] += 1

    if list_only:
        print(f"\n{'─'*60}")
        print(f"{'UUID':<36}  {'W':>5}  {'Moment'}")
        print(f"{'─'*60}")
        for row in rows:
            uuid = str(row["asset_uuid"] or "")
            w = row["width"] or 0
            moment = (row["moment_title"] or "").replace("\xa0", " ")
            found = "✓" if originals.get(uuid.upper()) else "✗"
            print(f"{uuid:<36}  {w:>5}  {found}  {moment}")
        print(f"\n  Toplam: {len(rows)} | Lokalda: {len(records)+len(missing)} | Eksik: {len(missing)}")
        return

    if not records:
        print("   Yerel dosya bulunamadı (iCloud'da olabilir).")
        if missing:
            print(f"   {len(missing)} resim iCloud'da: cloud_state={set(r['cloud_state'] for r in missing)}")
        return

    db = VisualMemoryDatabase(db_path)
    db.replace_index(records, enrichments)

    # Kalite sıralaması
    scored = sorted(
        zip(records, enrichments),
        key=lambda x: x[1].quality_score,
        reverse=True,
    )

    print(f"\n{'─'*60}")
    print(f"  {len(records)} resim indekslendi → {db_path.name}")
    print(f"  Boyut filtresi nedeniyle atlanan: {skipped_size}")
    print(f"  iCloud eksik: {len(missing)}")
    print(f"\n  En iyi {min(10, len(scored))} resim:")
    for i, (rec, enr) in enumerate(scored[:10], 1):
        print(f"  {i:>2}. [{enr.quality_score:.2f}] {rec.filename}  {rec.width}×{rec.height}  {enr.scene}  {enr.location}")

    print(f"\n  Moment dağılımı:")
    for moment, count in moments.most_common():
        print(f"    {count:>3}×  {moment}")

    manifest = {
        "location": location,
        "keywords": keywords,
        "rows_total": len(rows),
        "indexed": len(records),
        "missing_originals": len(missing),
        "skipped_small": skipped_size,
        "moments": dict(moments),
        "database": str(db_path),
    }
    log_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"\n  Log: {log_path.name}")


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mac Photos lokasyon tarayıcı")
    parser.add_argument("location", help="Arama terimi(leri), örn: 'Kızkalesi Mersin'")
    parser.add_argument("--list", action="store_true", help="Sadece listele, indeksleme yapma")
    parser.add_argument("--min-width", type=int, default=0, help="Minimum genişlik (px), örn: 1200")
    args = parser.parse_args()
    run(args.location, min_width=args.min_width, list_only=args.list)
