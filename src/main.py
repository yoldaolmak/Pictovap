#!/usr/bin/env python3
from __future__ import annotations

"""
YO OS Orchestrator — Main command handler
Parses user command and orchestrates full pipeline
"""

import re
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from src.core.media_quality import normalize_text, validate_metadata, validate_processed_asset
from src.utils.config import get_vil_dir, get_visual_memory_db_path, load_project_env

load_project_env()

from src.core.media_publish import build_publish_slug_candidates, embed_metadata, ensure_publish_path, ensure_unique_slug
from src.core.database import VisualMemoryComponent, VisualMemoryConfig
from src.core.processor import YOImageProcessor, get_vil_images
from src.core.metadata_generator import (
    YOMetadataGenerator,
    build_basic_metadata,
)
from src.services.wordpress import fetch_post_context, upload_images_batch

try:
    from src.core.cloud_vision import YOCloudVisionClient, generate_metadata_for_files as generate_gv_metadata
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


def search_semantic_assets(
    location_query: str,
    count: int,
    content_filter: str | None = None,
    post_context: Dict | None = None,
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

    # Sorguyu normalize et, tokenize et (≥3 char)
    normalized = _ascii_normalize(location_query)
    tokens = [t for t in re.split(r"\s+", normalized) if len(t) >= 3]
    if not tokens:
        return []

    # Her token için LIKE koşulu (AND — tüm tokenlar path'te aranır)
    like_parts = [f"LOWER(source_path) LIKE '%{t}%'" for t in tokens]
    location_sql = " AND ".join(like_parts)

    # İçerik filtresi SQL
    cf_key = _ascii_normalize(content_filter or "")
    canonical_cf = _FILTER_ALIASES.get(cf_key)
    content_sql = CONTENT_FILTER_SQL.get(canonical_cf or "", "") if canonical_cf else ""

    where = f"({location_sql}) AND is_personal = 0"
    if content_sql:
        where += f" AND {content_sql}"

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        sql = f"""
            SELECT source_path, filename, quality_score, selection_score,
                   activity, scene, location
            FROM asset_index
            WHERE {where}
            ORDER BY selection_score DESC, quality_score DESC
            LIMIT ?
        """
        rows = conn.execute(sql, [max(count * 4, 30)]).fetchall()
    finally:
        conn.close()

    # Post context varsa hero scoring ile yeniden sırala
    if post_context and rows:
        rows = sorted(rows, key=lambda r: _hero_score(r, post_context), reverse=True)

    paths: list[str] = []
    for row in rows:
        p = Path(row["source_path"])
        if p.exists():
            paths.append(str(p))
        if len(paths) >= count:
            break
    return paths


def load_vil_images_from_index(count: int | None = None, name: str | None = None) -> List[str]:
    return load_vil_images_from_index_for_post(count=count, name=name, post_context={})


def _tokenize_focus(text: str) -> list[str]:
    return [
        token for token in re.findall(r"[a-zA-Z0-9çğıöşüÇĞİÖŞÜ]+", str(text or "").lower())
        if len(token) >= 3
    ]


def _hero_score(row: Dict, post_context: Dict) -> float:
    score = float(row["quality_score"] or 0)
    title_tokens = _tokenize_focus(post_context.get("title", ""))
    slug_tokens = _tokenize_focus(str(post_context.get("slug", "")).replace("-", " "))
    focus_tokens = title_tokens[:6] + [token for token in slug_tokens if token not in title_tokens][:4]
    haystack = " ".join(
        [
            str(row["filename"] or "").lower(),
            str(row["title"] or "").lower(),
            str(row["description"] or "").lower(),
            str(row["location"] or "").lower(),
            str(row["activity"] or "").lower(),
            str(row["summary"] or "").lower(),
        ]
    )
    overlap = sum(1 for token in focus_tokens if token in haystack)
    score += overlap * 1.5
    if row["orientation"] == "landscape":
        score += 0.75
    if row["scene"] in {"landmark", "street", "nature"}:
        score += 0.5
    if row["activity"] in {"unknown", "portrait"}:
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
        """Log message"""
        print(message)

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
                from yo_unsplash import YOUnsplashDownloader

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
