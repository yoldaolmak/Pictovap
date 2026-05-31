from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from visual_memory.analyzer import analyze_image
from visual_memory.config import VisualMemoryConfig
from visual_memory.db import VisualMemoryDatabase
from visual_memory.enrich import enrich_record
from visual_memory.sources import DiscoveredImage


PHOTOS_DB = Path("~/Pictures/Photos Library.photoslibrary/database/Photos.sqlite").expanduser()
PHOTOS_ORIGINALS = Path("~/Pictures/Photos Library.photoslibrary/originals").expanduser()
ROME_DB = Path("/Users/KemalKaya/YO_OS_VIL/data/roma_mac_photos.sqlite")
LOG_PATH = Path("/Users/KemalKaya/YO_OS_VIL/ops_logs/2026-03-17_roma_mac_photos_index.log")
MANIFEST_PATH = Path("/Users/KemalKaya/YO_OS_VIL/ops_logs/2026-03-17_roma_mac_photos_manifest.json")
CURATION_PATH = Path("/Users/KemalKaya/YO_OS_VIL/examples/roma_mac_photos_curation.json")


ROME_QUERY = """
SELECT
    a.ZUUID AS asset_uuid,
    aa.ZORIGINALFILENAME AS original_filename,
    m.ZTITLE AS moment_title,
    m.ZUUID AS moment_uuid,
    a.ZCLOUDLOCALSTATE AS cloud_local_state,
    a.ZWIDTH AS width,
    a.ZHEIGHT AS height,
    a.ZDATECREATED AS date_created
FROM ZASSET a
JOIN ZMOMENT m ON m.Z_PK = a.ZMOMENT
LEFT JOIN ZADDITIONALASSETATTRIBUTES aa ON aa.Z_PK = a.ZADDITIONALATTRIBUTES
WHERE m.ZTITLE LIKE '%Rome%' OR m.ZTITLE LIKE '%Roma%' OR m.ZTITLE LIKE '%Romanum%'
ORDER BY a.ZDATECREATED;
"""


def iter_visible_originals(root: Path, allowed_suffixes: tuple[str, ...]) -> dict[str, Path]:
    by_stem: dict[str, Path] = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in allowed_suffixes:
            continue
        by_stem[path.stem.upper()] = path
    return by_stem


def load_rome_rows() -> list[sqlite3.Row]:
    connection = sqlite3.connect(PHOTOS_DB)
    connection.row_factory = sqlite3.Row
    try:
        return connection.execute(ROME_QUERY).fetchall()
    finally:
        connection.close()


def overlay_from_row(row: sqlite3.Row) -> dict[str, object]:
    moment_title = (row["moment_title"] or "").strip()
    keywords = ["rome", "roma", "italy", "italia", "mac_photos"]
    if moment_title:
        keywords.append(moment_title.lower().replace("\xa0", " "))
    return {
        "title": moment_title or None,
        "description": f"Photos moment: {moment_title}" if moment_title else "Photos moment: Rome",
        "keywords": keywords,
        "city": "Rome",
        "country": "Italy",
        "album_names": [moment_title] if moment_title else ["Rome"],
        "favorite": False,
    }


def load_curation() -> dict[str, dict[str, object]]:
    if not CURATION_PATH.exists():
        return {}
    payload = json.loads(CURATION_PATH.read_text() or "{}")
    if not isinstance(payload, dict):
        return {}
    return {str(key).upper(): value for key, value in payload.items() if isinstance(value, dict)}


def apply_curation(record, enrichment, curation: dict[str, object]):
    extra_keywords = [str(item).strip() for item in curation.get("keywords", []) if str(item).strip()]
    extra_album_names = [str(item).strip() for item in curation.get("album_names", []) if str(item).strip()]
    extra_places = [str(item).strip() for item in curation.get("places", []) if str(item).strip()]
    extra_people = [str(item).strip() for item in curation.get("people", []) if str(item).strip()]
    extra_story_tags = [str(item).strip() for item in curation.get("story_tags", []) if str(item).strip()]

    if isinstance(curation.get("title"), str) and curation["title"].strip():
        record.title = curation["title"].strip()
    if isinstance(curation.get("description"), str) and curation["description"].strip():
        record.description = curation["description"].strip()

    record.keywords = sorted(set(record.keywords + extra_keywords + extra_places + extra_people))
    record.album_names = sorted(set(record.album_names + extra_album_names))

    enrichment.objects = sorted(set(enrichment.objects + extra_places))
    enrichment.keywords = sorted(set(enrichment.keywords + extra_keywords + extra_places + extra_people))
    enrichment.places = sorted(set(enrichment.places + extra_places))
    enrichment.people = sorted(set(enrichment.people + extra_people))
    enrichment.story_tags = sorted(set(enrichment.story_tags + extra_story_tags))

    if extra_places and enrichment.location == "Rome, Italy":
        enrichment.location = ", ".join(extra_places)
    if isinstance(curation.get("scene"), str) and curation["scene"].strip():
        enrichment.scene = curation["scene"].strip()
    if isinstance(curation.get("activity"), str) and curation["activity"].strip():
        enrichment.activity = curation["activity"].strip()

    summary_bits = [record.title or record.filename, enrichment.scene, enrichment.location]
    if enrichment.people:
        summary_bits.append("people: " + ", ".join(enrichment.people))
    enrichment.summary = " | ".join(bit for bit in summary_bits if bit)
    return record, enrichment


def main() -> None:
    config = VisualMemoryConfig(database_path=ROME_DB, scan_photos_library=False, external_roots=[])
    originals_by_stem = iter_visible_originals(PHOTOS_ORIGINALS, config.image_extensions)
    rome_rows = load_rome_rows()
    curation_by_uuid = load_curation()

    records = []
    enrichments = []
    missing = []
    matched_moments: Counter[str] = Counter()

    for row in rome_rows:
        asset_uuid = row["asset_uuid"]
        if not asset_uuid:
            continue
        original_path = originals_by_stem.get(str(asset_uuid).upper())
        if original_path is None:
            missing.append(
                {
                    "asset_uuid": asset_uuid,
                    "original_filename": row["original_filename"],
                    "moment_title": row["moment_title"],
                    "cloud_local_state": row["cloud_local_state"],
                }
            )
            continue

        record = analyze_image(
            DiscoveredImage(path=original_path, source_type="mac_photos"),
            photos_overlay=overlay_from_row(row),
        )
        enrichment = enrich_record(record)
        curation = curation_by_uuid.get(str(asset_uuid).upper())
        if curation:
            record, enrichment = apply_curation(record, enrichment, curation)
        records.append(record)
        enrichments.append(enrichment)
        matched_moments[(row["moment_title"] or "unknown").replace("\xa0", " ")] += 1

    database = VisualMemoryDatabase(ROME_DB)
    database.replace_index(records, enrichments)

    manifest = {
        "database_path": str(ROME_DB),
        "source": "mac_photos_rome_only",
        "rome_rows_total": len(rome_rows),
        "indexed_records": len(records),
        "missing_originals": len(missing),
        "curated_records": sum(1 for row in rome_rows if str(row["asset_uuid"]).upper() in curation_by_uuid),
        "moments": dict(matched_moments),
        "missing_preview": missing[:50],
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=True, indent=2))

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(
        "\n".join(
            [
                "timestamp: 2026-03-17",
                "operation: rome_mac_photos_index",
                f"database: {ROME_DB}",
                f"rome_rows_total: {len(rome_rows)}",
                f"indexed_records: {len(records)}",
                f"missing_originals: {len(missing)}",
                f"moments: {dict(matched_moments)}",
                f"manifest: {MANIFEST_PATH}",
            ]
        )
        + "\n"
    )

    print(json.dumps(manifest, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
