#!/usr/bin/env python3
"""
YO OS — Mac Photos akıllı filtre (Apple ML tabanlı, sıfır API maliyeti)

Filtre katmanları:
  1. Moment filtresi     — ev/mahalle momentlerini çıkar
  2. Boyut filtresi      — min genişlik
  3. Kalite filtresi     — Apple blur + exposure skoru (ücretsiz)
  4. Yüz/aile filtresi   — face count + tanınan aile üyeleri (ücretsiz)
  5. Sahne filtresi      — Apple scene classification (ücretsiz, decode edilmiş)
  6. Duplikat eleme      — burst/seri çekim → en iyisini tut
  7. Blogger skoru       — Kemal Kaya gözüyle 0–1 skor

Kullanım:
  python3 yo_photo_filter.py [--dry-run] [--min-width 1200] [--since 2020]
"""
from __future__ import annotations

import argparse
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR     = PROJECT_ROOT / "data"
OPS_DIR      = PROJECT_ROOT / "ops_logs"
OUT_DB       = DATA_DIR / "photo_candidates.sqlite"

PHOTOS_DB        = Path("~/Pictures/Photos Library.photoslibrary/database/Photos.sqlite").expanduser()
PHOTOS_ORIGINALS = Path("~/Pictures/Photos Library.photoslibrary/originals").expanduser()
CD_EPOCH         = datetime(2001, 1, 1).timestamp()
IMAGE_EXT        = {".jpg", ".jpeg", ".heic", ".png", ".tiff", ".dng", ".raw"}


# ── Apple Scene ID Haritası (reverse-engineered) ─────────────────────────────
# NOT: 2147483381 ve 2147482365 base flag — neredeyse her fotoğrafta var, filtre için kullanma

# 0 yüz ağırlıklı + seyahat destination'larında yüksek → OUTDOOR/TRAVEL (skor bonusu)
SCENE_OUTDOOR = {
    2147482623,   # outdoor landscape (Nevşehir, Elâzığ, Antalya, Muğla)
    -2147483641,  # outdoor / nature
    1222,         # outdoor / travel scene
    383,          # mountain / landscape
    229,          # beach / coast
    784,          # forest / nature
    130,          # architecture / building
    1535,         # outdoor travel
}

# Yüz ağırlıklı + Home/Menemen/Karşıyaka dominant → PORTRAIT/SOCIAL
# Yalnızca face_count >= 1 ile birlikte filtre olarak kullan
SCENE_PORTRAIT = {
    881,          # portrait / people
    1600,         # portrait
    595,          # group / social
    382,          # selfie / close portrait
    1345,         # social gathering
    1441,         # family scene
    1346,         # family
    1008,         # indoor social
    -2147483643,  # indoor / home
}


# ── Filtre Listeleri ─────────────────────────────────────────────────────────

EXCLUDE_MOMENTS = {
    "home", "menemen", "karşıyaka", "karsiyaka", "buca", "cigli", "çiğli",
    "istinye park", "yesilyurt", "battalgazi", "yesilyurt & battalgazi",
    "cigli & karsiyaka", "bornova", "bayrakli", "bayraklı",
    "konak", "bostanli", "bostanlı", "narlidere", "narlıdere",
    "gaziemir", "torbalı", "torbali", "kınık", "aliaga", "aliağa",
}

# Bu kişilerden biri fotoğrafta varsa → aile fotoğrafı → çıkar
FAMILY_PERSONS = {"Ayisha Guliyeva", "Ella", "Sevgül Kaya", "Kıymet Kaya"}

HIGH_VALUE_MOMENTS = {
    "kapadokya", "cappadocia", "nevşehir", "nevsehir", "göreme",
    "antalya", "muğla", "mugla", "bodrum", "fethiye", "pamukkale",
    "efes", "nemrut", "sinop", "çanakkale", "canakkale", "trabzon",
    "mardin", "şanlıurfa", "gaziantep", "hatay", "kaş", "kas",
    "kekova", "olympos", "olimpos", "anamur", "mersin", "silifke",
    "tunceli", "elazığ", "elazig", "malatya", "sivas", "afyon",
    "erzurum", "kars", "van", "diyarbakır", "diyarbakir",
    "rome", "roma", "florence", "firenze", "venice", "venezia",
    "naples", "napoli", "caprarola", "san gimignano", "montepulciano",
    "padua", "ischia", "valletta", "victoria", "vittoriosa",
    "baku", "bakü", "shaki", "şeki", "qax", "astana", "charyn",
    "krabi", "chiang mai", "phuket", "sharm", "tunceli", "dersim",
}


# ── Yardımcılar ──────────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", (text or "").lower())
    return nfkd.encode("ascii", "ignore").decode("ascii")


def _is_excluded_moment(title: str | None) -> bool:
    if title is None:
        return True
    return _norm(title) in EXCLUDE_MOMENTS


def _is_high_value_moment(title: str | None) -> bool:
    if not title:
        return False
    t = _norm(title)
    return any(dest in t for dest in HIGH_VALUE_MOMENTS)


# ── Veritabanı Sorguları ─────────────────────────────────────────────────────

def load_all_data(since_ts: float) -> list[dict]:
    """
    Photos.sqlite'dan tek JOIN ile tüm gerekli veriyi çek:
    moment, boyut, GPS, Apple kalite skorları, yüz sayısı, scene ID'leri
    """
    conn = sqlite3.connect(PHOTOS_DB)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT
            a.Z_PK           AS asset_pk,
            a.ZUUID          AS uuid,
            aa.ZORIGINALFILENAME AS filename,
            m.ZTITLE         AS moment,
            a.ZWIDTH         AS w,
            a.ZHEIGHT        AS h,
            a.ZLATITUDE      AS lat,
            a.ZLONGITUDE     AS lon,
            a.ZDATECREATED   AS date,
            a.ZCLOUDLOCALSTATE AS cloud,
            ma.ZFACECOUNT    AS face_count,
            ma.ZBLURRINESSSCORE  AS blur,
            ma.ZEXPOSURESCORE    AS exposure
        FROM ZASSET a
        JOIN ZMOMENT m ON m.Z_PK = a.ZMOMENT
        LEFT JOIN ZADDITIONALASSETATTRIBUTES aa ON aa.Z_PK = a.ZADDITIONALATTRIBUTES
        LEFT JOIN ZMEDIAANALYSISASSETATTRIBUTES ma ON ma.ZASSET = a.Z_PK
        WHERE a.ZKIND = 0 AND a.ZDATECREATED >= ?
        ORDER BY a.ZDATECREATED
    """, (since_ts,)).fetchall()

    # Scene ID'lerini toplu çek (her asset için en yüksek confidence)
    scene_map: dict[int, set[int]] = {}
    scene_rows = conn.execute("""
        SELECT sc.ZASSETATTRIBUTES, sc.ZSCENEIDENTIFIER
        FROM ZSCENECLASSIFICATION sc
        JOIN ZADDITIONALASSETATTRIBUTES aa ON aa.Z_PK = sc.ZASSETATTRIBUTES
        JOIN ZASSET a ON a.ZADDITIONALATTRIBUTES = aa.Z_PK
        WHERE a.ZKIND=0 AND a.ZDATECREATED >= ? AND sc.ZCONFIDENCE >= 0.6
    """, (since_ts,)).fetchall()
    for sr in scene_rows:
        scene_map.setdefault(sr[0], set()).add(sr[1])

    # Aile üyesi olan asset'leri bul
    family_assets: set[int] = set()
    for name in FAMILY_PERSONS:
        frows = conn.execute("""
            SELECT DISTINCT f.ZASSET
            FROM ZDETECTEDFACE f
            JOIN ZPERSON p ON p.Z_PK = f.ZPERSON
            WHERE p.ZFULLNAME = ?
        """, (name,)).fetchall()
        for fr in frows:
            family_assets.add(fr[0])

    conn.close()

    # Dict'e çevir, scene ve aile bilgisini ekle
    result = []
    for row in rows:
        aa_pk = None  # scene_map key = ZASSETATTRIBUTES pk
        # scene_map'i asset_pk üzerinden değil aa_pk üzerinden tutuyoruz
        # row'da ZADDITIONALATTRIBUTES yok ama aa join'den geliyor
        # Yeniden sorgu yerine: scene_map'i asset_pk ile de eşleştirelim
        result.append({
            "asset_pk":  row["asset_pk"],
            "uuid":      row["uuid"],
            "filename":  row["filename"],
            "moment":    row["moment"],
            "w":         row["w"] or 0,
            "h":         row["h"] or 0,
            "lat":       row["lat"],
            "lon":       row["lon"],
            "date":      row["date"],
            "cloud":     row["cloud"],
            "face_count": row["face_count"] or 0,
            "blur":       row["blur"] or 0.5,
            "exposure":   row["exposure"] or 0.5,
            "has_family": row["asset_pk"] in family_assets,
            "scenes":     set(),  # sonraki adımda doldurulacak
        })

    return result, scene_map


def attach_scenes(records: list[dict], scene_map: dict) -> None:
    """scene_map (ZASSETATTRIBUTES → set[scene_id]) → records'a ekle.
    Maalesef JOIN olmadan ZASSETATTRIBUTES PK'yı bilmiyoruz,
    bu yüzden UUID üzerinden ikinci bir sorgu yapıyoruz."""
    conn = sqlite3.connect(PHOTOS_DB)
    conn.row_factory = sqlite3.Row

    # asset_pk → aa_pk eşlemesi
    since_ts = min(r["date"] for r in records if r["date"]) - 1
    pk_map = {}
    for row in conn.execute("""
        SELECT a.Z_PK as apk, a.ZADDITIONALATTRIBUTES as aapk
        FROM ZASSET a WHERE a.ZKIND=0 AND a.ZDATECREATED >= ?
    """, (since_ts,)).fetchall():
        pk_map[row["apk"]] = row["aapk"]

    conn.close()

    for rec in records:
        aa_pk = pk_map.get(rec["asset_pk"])
        rec["scenes"] = scene_map.get(aa_pk, set()) if aa_pk else set()


# ── Blogger Skoru ────────────────────────────────────────────────────────────

def blogger_score(rec: dict) -> float:
    score = 0.0
    w, h   = rec["w"], rec["h"]
    moment = _norm(rec["moment"] or "")
    lat, lon = rec["lat"], rec["lon"]
    scenes   = rec["scenes"]
    blur     = rec["blur"]
    exposure = rec["exposure"]

    # Çözünürlük (0.20)
    if w >= 4000:   score += 0.20
    elif w >= 3000: score += 0.16
    elif w >= 2000: score += 0.10
    else:           score += 0.04

    # Netlik + pozlama (0.15)
    score += min(0.15, ((blur + exposure) / 2) * 0.15)

    # Yatay oryantasyon (0.10)
    if w > h:
        score += 0.10

    # Apple scene: outdoor bonus (0.20)
    if scenes & SCENE_OUTDOOR:
        score += 0.20
    # Portrait/sosyal ceza: yüz varsa ekstra düşür
    if (scenes & SCENE_PORTRAIT) and rec["face_count"] >= 1:
        score -= 0.15

    # GPS seyahat bölgesi (0.10)
    if lat and lon:
        in_izmir_home = (38.3 <= lat <= 38.7) and (26.8 <= lon <= 27.3)
        if not in_izmir_home:
            score += 0.10

    # Yüksek değer moment (0.15)
    if _is_high_value_moment(rec["moment"]):
        score += 0.15

    # Yurt dışı bonus (0.10)
    if lat and lon:
        in_turkey = (36.0 <= lat <= 42.5) and (26.0 <= lon <= 44.8)
        if not in_turkey:
            score += 0.10

    return min(1.0, round(score, 3))


# ── Duplikat Eleme ───────────────────────────────────────────────────────────

def dedup(records: list[dict]) -> tuple[list[dict], int]:
    from collections import defaultdict
    buckets: dict[tuple, list] = defaultdict(list)
    for rec in records:
        moment  = rec["moment"] or "__none__"
        ts_buck = int((rec["date"] or 0) / 3)
        buckets[(moment, ts_buck)].append(rec)

    kept, removed = [], 0
    for group in buckets.values():
        if len(group) == 1:
            kept.append(group[0])
        else:
            best = max(group, key=lambda r: r["w"] * r["h"])
            kept.append(best)
            removed += len(group) - 1
    return kept, removed


# ── Yerel Dosya Dizini ───────────────────────────────────────────────────────

def iter_originals() -> dict[str, Path]:
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


# ── Çıktı DB ─────────────────────────────────────────────────────────────────

def create_output_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            uuid            TEXT PRIMARY KEY,
            filename        TEXT,
            local_path      TEXT,
            moment          TEXT,
            width           INTEGER,
            height          INTEGER,
            orientation     TEXT,
            latitude        REAL,
            longitude       REAL,
            date_created    REAL,
            blur_score      REAL,
            exposure_score  REAL,
            face_count      INTEGER,
            has_family      INTEGER,
            scene_ids       TEXT,
            blogger_score   REAL,
            vision_done     INTEGER DEFAULT 0,
            vision_labels   TEXT,
            filter_reason   TEXT
        )
    """)
    conn.commit()
    return conn


# ── Ana Pipeline ─────────────────────────────────────────────────────────────

def run(min_width: int = 1200, since_year: int = 2020, dry_run: bool = False) -> None:
    since_ts = datetime(since_year, 1, 1).timestamp() - CD_EPOCH

    print(f"\n{'='*62}")
    print(f"  YO Photo Filter  |  {since_year}+  |  min {min_width}px  {'[DRY RUN]' if dry_run else ''}")
    print(f"{'='*62}")

    # 1. Veri yükle
    print("\n[1/6] Photos DB okunuyor...")
    records, scene_map = load_all_data(since_ts)
    print(f"  Ham fotoğraf: {len(records):,}")

    print("  Scene ID'leri eşleştiriliyor...")
    attach_scenes(records, scene_map)

    # 2. Moment + boyut filtresi
    print("\n[2/6] Moment ve boyut filtresi...")
    r2, excl_moment, excl_size = [], 0, 0
    for rec in records:
        if _is_excluded_moment(rec["moment"]):
            excl_moment += 1
            continue
        if rec["w"] < min_width:
            excl_size += 1
            continue
        r2.append(rec)
    print(f"  Ev/mahalle elendi : {excl_moment:,}")
    print(f"  Boyut < {min_width}px  : {excl_size:,}")
    print(f"  Kalan             : {len(r2):,}")

    # 3. Apple kalite filtresi
    print("\n[3/6] Apple kalite filtresi (blur + exposure)...")
    r3, excl_blur, excl_exp = [], 0, 0
    for rec in r2:
        if rec["blur"] < 0.55:
            excl_blur += 1
            continue
        if rec["exposure"] < 0.55:
            excl_exp += 1
            continue
        r3.append(rec)
    print(f"  Bulanık elendi  : {excl_blur:,}")
    print(f"  Karanlık elendi : {excl_exp:,}")
    print(f"  Kalan           : {len(r3):,}")

    # 4. Yüz + aile filtresi
    print("\n[4/6] Yüz ve aile filtresi...")
    r4, excl_family, excl_crowd = [], 0, 0
    for rec in r3:
        if rec["has_family"]:
            excl_family += 1
            continue
        if rec["face_count"] >= 3:
            excl_crowd += 1
            continue
        r4.append(rec)
    print(f"  Aile üyesi fotoğrafı elendi : {excl_family:,}")
    print(f"  Kalabalık (3+ yüz) elendi  : {excl_crowd:,}")
    print(f"  Kalan                       : {len(r4):,}")

    # 5. Apple sahne filtresi
    print("\n[5/6] Apple sahne filtresi...")
    r5, excl_scene = [], 0
    for rec in r4:
        scenes = rec["scenes"]
        # Portrait scene + yüz var + outdoor scene YOK → çıkar
        is_portrait_only = bool(scenes & SCENE_PORTRAIT) and not bool(scenes & SCENE_OUTDOOR)
        if is_portrait_only and rec["face_count"] >= 1:
            excl_scene += 1
            continue
        r5.append(rec)
    print(f"  Portrait/sosyal sahne elendi: {excl_scene:,}")
    print(f"  Kalan                       : {len(r5):,}")

    # 6. Duplikat eleme
    print("\n[6/6] Duplikat/burst eleme + skorlama...")
    r6, deduped = dedup(r5)
    print(f"  Burst/seri elendi: {deduped:,}")
    print(f"  Kalan            : {len(r6):,}")

    # Skor hesapla
    for rec in r6:
        rec["score"] = blogger_score(rec)
    r6.sort(key=lambda r: r["score"], reverse=True)

    dist = {"≥0.8": 0, "0.6-0.8": 0, "0.4-0.6": 0, "<0.4": 0}
    for rec in r6:
        s = rec["score"]
        if s >= 0.8:    dist["≥0.8"] += 1
        elif s >= 0.6:  dist["0.6-0.8"] += 1
        elif s >= 0.4:  dist["0.4-0.6"] += 1
        else:           dist["<0.4"] += 1

    print(f"\n  Skor dağılımı:")
    print(f"    Mükemmel ≥0.8  : {dist['≥0.8']:,}")
    print(f"    İyi     0.6-0.8: {dist['0.6-0.8']:,}")
    print(f"    Orta    0.4-0.6: {dist['0.4-0.6']:,}")
    print(f"    Düşük   <0.4   : {dist['<0.4']:,}")

    # En iyi 15
    print(f"\n  {'Skor':>5}  {'W':>5}  {'Yüz':>3}  {'Moment'}")
    print(f"  {'─'*55}")
    for rec in r6[:15]:
        sc_mark = "★" if rec["scenes"] & SCENE_OUTDOOR else " "
        print(f"  {rec['score']:>5.2f}{sc_mark} {rec['w']:>5}  {rec['face_count']:>3}  {rec['moment'] or '(?)'}")

    # DB'ye yaz
    if not dry_run:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        originals = iter_originals()
        out_conn  = create_output_db(OUT_DB)
        out_conn.execute("DELETE FROM candidates")

        local_n, cloud_n = 0, 0
        for rec in r6:
            uuid_up   = (rec["uuid"] or "").upper()
            local_path = originals.get(uuid_up)
            orient     = "landscape" if rec["w"] > rec["h"] else "portrait"
            out_conn.execute("""
                INSERT OR REPLACE INTO candidates
                (uuid, filename, local_path, moment, width, height, orientation,
                 latitude, longitude, date_created, blur_score, exposure_score,
                 face_count, has_family, scene_ids, blogger_score)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                rec["uuid"], rec["filename"],
                str(local_path) if local_path else None,
                rec["moment"], rec["w"], rec["h"], orient,
                rec["lat"], rec["lon"], rec["date"],
                rec["blur"], rec["exposure"],
                rec["face_count"], int(rec["has_family"]),
                ",".join(str(s) for s in rec["scenes"]),
                rec["score"],
            ))
            if local_path: local_n += 1
            else:          cloud_n += 1

        out_conn.commit()
        out_conn.close()
        print(f"\n  DB yazıldı: {OUT_DB}")
        print(f"  Lokalda: {local_n:,}  |  iCloud: {cloud_n:,}")

    # Vision maliyet tahmini
    vision_n   = sum(1 for r in r6 if r["score"] >= 0.6)
    cost_usd   = max(0, vision_n * 4 - 1000) / 1000 * 1.50
    total_saved = len(records) - vision_n

    print(f"\n{'─'*62}")
    print(f"  Ham                        : {len(records):,}")
    print(f"  Filtre sonrası             : {len(r6):,}")
    print(f"  Vision için uygun (≥0.6)   : {vision_n:,}")
    print(f"  Elenen (Vision gerekmez)   : {total_saved:,}  (%{total_saved/len(records)*100:.0f})")
    print(f"  Tahmini Vision maliyeti    : ${cost_usd:.2f}  (~{cost_usd*35:.0f} TL)")
    print(f"{'─'*62}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-width", type=int, default=1200)
    parser.add_argument("--since",     type=int, default=2020)
    parser.add_argument("--dry-run",   action="store_true")
    args = parser.parse_args()
    run(min_width=args.min_width, since_year=args.since, dry_run=args.dry_run)
