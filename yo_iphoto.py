#!/usr/bin/env python3
"""
YO OS — Mac Photos akıllı arama komutu

Sözdizimi:
  [N] [en iyi] [dikey|yatay] [KİŞİ,] LOKASYON iphoto[;MIN_SKOR]

Örnekler:
  5 floransa iphoto
  en iyi dikey 3 alaçatı iphoto
  en iyi dikey 3 alaçatı iphoto;3
  Kemal, Olimpos iphoto
  10 yatay istanbul iphoto;4
"""
from __future__ import annotations

import re
import sqlite3
import subprocess
import sys
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from visual_memory.analyzer import analyze_image
from visual_memory.enrich import enrich_record
from visual_memory.sources import DiscoveredImage

PHOTOS_DB        = Path("~/Pictures/Photos Library.photoslibrary/database/Photos.sqlite").expanduser()
PHOTOS_ORIGINALS = Path("~/Pictures/Photos Library.photoslibrary/originals").expanduser()
IMAGE_EXT        = {".jpg", ".jpeg", ".heic", ".png", ".tiff", ".raw", ".dng"}


# ── Normalize ────────────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return nfkd.encode("ascii", "ignore").decode("ascii")


# ── Komut Ayrıştırıcı ────────────────────────────────────────────────────────

def parse_command(cmd: str) -> dict:
    """
    Döner:
      count       : int | None
      orientation : "portrait" | "landscape" | None
      location    : str
      person      : str | None
      min_score   : float (0.0 – 1.0, ;1-5 → /5)
    """
    cmd = cmd.strip()

    # ;MIN_SKOR ayır
    min_score = 0.0
    m = re.search(r";(\d+(?:\.\d+)?)\s*$", cmd)
    if m:
        raw = float(m.group(1))
        min_score = raw / 5.0 if raw > 1.0 else raw
        cmd = cmd[: m.start()].strip()

    # "iphoto" son kısmı temizle
    cmd = re.sub(r"\s*iphoto\s*$", "", cmd, flags=re.IGNORECASE).strip()

    # KİŞİ, LOKASYON — virgülle ayrılmış kişi varsa
    person = None
    m = re.match(r"^([A-ZÇĞİÖŞÜa-zçğışöüâêîûI][^,]{0,30}),\s*(.+)$", cmd)
    if m:
        person = m.group(1).strip()
        cmd = m.group(2).strip()

    # Sayı
    count = None
    m = re.match(r"^(\d+)\s+", cmd)
    if m:
        count = int(m.group(1))
        cmd = cmd[m.end():].strip()

    # "en iyi" prefix
    cmd = re.sub(r"^en\s+iyi\s+", "", cmd, flags=re.IGNORECASE).strip()

    # Sayı (başa değil ortaya yazılmışsa)
    if count is None:
        m = re.match(r"^(\d+)\s+", cmd)
        if m:
            count = int(m.group(1))
            cmd = cmd[m.end():].strip()

    # Yön
    orientation = None
    m = re.match(r"^(dikey|yatay|portrait|landscape|vertical|horizontal)\s+", cmd, re.IGNORECASE)
    if m:
        o = m.group(1).lower()
        orientation = "portrait" if o in ("dikey", "portrait", "vertical") else "landscape"
        cmd = cmd[m.end():].strip()

    # Sayı sonda da olabilir: "adamkayalar 3"
    if count is None:
        m = re.search(r"\s+(\d+)\s*$", cmd)
        if m:
            count = int(m.group(1))
            cmd = cmd[: m.start()].strip()

    # Kalan = lokasyon
    location = cmd.strip()
    return {
        "count": count,
        "orientation": orientation,
        "location": location,
        "person": person,
        "min_score": min_score,
    }


# ── Photos DB ────────────────────────────────────────────────────────────────

def _iter_originals() -> dict[str, Path]:
    by_uuid: dict[str, Path] = {}
    if not PHOTOS_ORIGINALS.exists():
        return by_uuid
    for path in PHOTOS_ORIGINALS.rglob("*"):
        rel = path.relative_to(PHOTOS_ORIGINALS)
        if any(p.startswith(".") for p in rel.parts):
            continue
        if path.is_file() and path.suffix.lower() in IMAGE_EXT:
            by_uuid[path.stem.upper()] = path
    return by_uuid


def _search_photos_db(location: str, person: str | None) -> list[sqlite3.Row]:
    if not PHOTOS_DB.exists():
        print(f"⚠️  Photos Library bulunamadı: {PHOTOS_DB}")
        return []

    keywords = location.split() + (person.split() if person else [])
    conds = " OR ".join("m.ZTITLE LIKE ?" for _ in keywords)
    sql = f"""
    SELECT
        a.ZUUID            AS uuid,
        aa.ZORIGINALFILENAME AS filename,
        m.ZTITLE           AS moment,
        a.ZWIDTH           AS w,
        a.ZHEIGHT          AS h,
        a.ZCLOUDLOCALSTATE AS cloud
    FROM ZASSET a
    JOIN ZMOMENT m ON m.Z_PK = a.ZMOMENT
    LEFT JOIN ZADDITIONALASSETATTRIBUTES aa ON aa.Z_PK = a.ZADDITIONALATTRIBUTES
    WHERE {conds}
    ORDER BY a.ZDATECREATED DESC
    """
    conn = sqlite3.connect(PHOTOS_DB)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(sql, [f"%{kw}%" for kw in keywords]).fetchall()
    finally:
        conn.close()


# ── Ana Fonksiyon ─────────────────────────────────────────────────────────────

def run(cmd: str) -> None:
    p = parse_command(cmd)
    location    = p["location"]
    person      = p["person"]
    count       = p["count"]
    orientation = p["orientation"]
    min_score   = p["min_score"]

    label_parts = []
    if person:
        label_parts.append(f"kişi={person}")
    label_parts.append(f"lokasyon={location}")
    if orientation:
        label_parts.append(orientation)
    if count:
        label_parts.append(f"max={count}")
    if min_score:
        label_parts.append(f"min_skor={min_score:.1f}")
    print(f"\n🔍 {' | '.join(label_parts)}")

    rows = _search_photos_db(location, person)
    print(f"   Photos DB: {len(rows)} sonuç")

    if not rows:
        print("   Sonuç yok.")
        return

    originals = _iter_originals()

    # Sadece lokal olanları al
    candidates = []
    missing_cloud = 0
    for row in rows:
        uuid = (row["uuid"] or "").upper()
        path = originals.get(uuid)
        if path is None:
            missing_cloud += 1
            continue
        w = row["w"] or 0
        h = row["h"] or 0
        candidates.append({"uuid": uuid, "path": path, "w": w, "h": h, "moment": row["moment"]})

    print(f"   Lokal: {len(candidates)} | iCloud: {missing_cloud}")

    if not candidates:
        print("   Lokal dosya bulunamadı. Photos → Tümünü İndir yapılabilir.")
        return

    # Analiz + enrich
    scored = []
    for c in candidates:
        record = analyze_image(
            DiscoveredImage(path=c["path"], source_type="mac_photos"),
            photos_overlay={"keywords": [location.lower()], "city": location},
        )
        enrichment = enrich_record(record)
        scored.append((record, enrichment, c))

    # Yön filtresi
    if orientation:
        scored = [
            (r, e, c) for r, e, c in scored
            if e.orientation == orientation
        ]
        print(f"   Yön filtresi ({orientation}): {len(scored)} kaldı")

    # Kişi filtresi (keyword veya dosya adı içinde)
    if person:
        person_norm = _norm(person)
        scored = [
            (r, e, c) for r, e, c in scored
            if person_norm in _norm(r.search_document())
        ]
        print(f"   Kişi filtresi ({person}): {len(scored)} kaldı")

    # Min skor filtresi
    if min_score > 0:
        scored = [(r, e, c) for r, e, c in scored if e.quality_score >= min_score]
        print(f"   Min skor ({min_score:.1f}): {len(scored)} kaldı")

    # Kaliteye göre sırala
    scored.sort(key=lambda x: x[1].quality_score, reverse=True)

    # Count sınırı
    if count:
        scored = scored[:count]

    if not scored:
        print("   Filtreler sonrası sonuç kalmadı.")
        return

    # Sonuçları göster + aç
    print(f"\n   {'#':<3} {'Skor':>5}  {'Yön':<10}  {'Boyut':<12}  {'Moment'}")
    print(f"   {'─'*60}")
    paths_to_open = []
    for i, (rec, enr, c) in enumerate(scored, 1):
        dim = f"{rec.width}×{rec.height}" if rec.width else "?"
        print(f"   {i:<3} {enr.quality_score:>5.2f}  {enr.orientation:<10}  {dim:<12}  {c['moment'] or ''}")
        paths_to_open.append(str(c["path"]))

    print()
    subprocess.run(["open"] + paths_to_open)
    print(f"   ✓ {len(paths_to_open)} fotoğraf Preview'da açıldı")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    run(" ".join(sys.argv[1:]))
