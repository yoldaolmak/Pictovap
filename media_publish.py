from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict


BAD_SLUG_TOKENS = {
    "depositphotos",
    "xl",
    "yo",
    "processed",
    "final",
    "new",
    "image",
    "img",
    "dsc",
    "untitled",
    "webp",
}
FORBIDDEN_FALLBACK_TOKENS = {"genel", "gorsel", "gorunum", "gorunumu"}

GENERIC_POST_TOKENS = {
    "gezi",
    "gezilecek",
    "yerler",
    "yerleri",
    "rehberi",
    "rota",
    "rotasi",
    "rotalari",
    "seyahat",
    "travel",
    "guide",
    "itinerary",
    "kisisel",
    "deneyimler",
    "deneyim",
    "guncel",
    "genel",
    "detayli",
    "detay",
    "liste",
    "notlari",
    "notlar",
    "ve",
    "ile",
    "icin",
    "the",
    "and",
    "2024",
    "2025",
    "2026",
    "2027",
}

GENERIC_SCENE_TOKENS = {
    "landmark",
    "neighbourhood",
    "neighborhood",
    "body",
    "water",
    "street",
    "city",
    "town",
    "place",
    "view",
    "scenery",
    "travel",
    "tourism",
    "location",
    "destination",
    "image",
    "photo",
    "photography",
    "plants",
    "plant",
    "produce",
    "food",
    "train",
    "tire",
    "outdoor",
    "vehicle",
    "gorunum",
    "gorunumu",
    "viewpoint",
}

GENERIC_SOURCE_TOKENS = {
    "a",
    "an",
    "along",
    "ancient",
    "around",
    "architecture",
    "asia",
    "asian",
    "attraction",
    "background",
    "beautiful",
    "building",
    "capital",
    "city",
    "cityscape",
    "cloud",
    "colorful",
    "culture",
    "danger",
    "dangerous",
    "destination",
    "direct",
    "environment",
    "europe",
    "famous",
    "field",
    "float",
    "fog",
    "holiday",
    "historic",
    "history",
    "home",
    "house",
    "in",
    "incredible",
    "indochina",
    "is",
    "jungle",
    "landmark",
    "landscape",
    "life",
    "local",
    "long",
    "middle",
    "mist",
    "natural",
    "nature",
    "old",
    "outdoor",
    "panorama",
    "panoramic",
    "peaceful",
    "people",
    "person",
    "persons",
    "woman",
    "women",
    "man",
    "men",
    "girl",
    "girls",
    "boy",
    "boys",
    "lady",
    "ladies",
    "adult",
    "adults",
    "perspective",
    "picture",
    "poor",
    "poverty",
    "reflections",
    "relaxation",
    "road",
    "romantic",
    "running",
    "safety",
    "scenic",
    "sea",
    "security",
    "seascape",
    "silhouette",
    "site",
    "southeast",
    "south",
    "strange",
    "street",
    "summer",
    "taking",
    "through",
    "to",
    "tour",
    "tourism",
    "tourist",
    "tourists",
    "traditional",
    "tranquil",
    "transport",
    "transportation",
    "travel",
    "traveler",
    "trip",
    "unesco",
    "unusual",
    "urban",
    "vacation",
    "vietnamese",
    "view",
    "village",
    "way",
    "with",
    "world",
    "heritage",
    "site",
    "shrub",
    "tree",
    "trees",
    "leaf",
    "leaves",
    "flora",
    "world",
    "asya",
    "avrupa",
    "afrika",
    "okyanusya",
    "ortadogu",
    "other",
    "volumes",
    "lacie",
    "travel",
    "turkiye",
    "endonezya",
    "indonesia",
    "borneo",
    "filipinler",
    "malaysia",
    "thailand",
    "japan",
    "china",
    "india",
}

SCENE_REMAP = {
    "beach": "sahil",
    "coast": "kiyi",
    "ocean": "deniz",
    "bay": "korfezi",
    "harbor": "liman",
    "port": "liman",
    "boat": "tekne",
    "ship": "tekne",
    "junk": "tekne",
    "junks": "tekne",
    "island": "ada",
    "bridge": "kopru",
    "river": "nehir",
    "lake": "gol",
    "mountain": "dag",
    "forest": "orman",
    "nature": "doga",
    "landscape": "manzara",
    "sunset": "gunbatimi",
    "sunrise": "gundogumu",
    "night": "gece",
    "market": "pazar",
    "temple": "tapinak",
    "pagoda": "pagoda",
    "palace": "saray",
    "castle": "kale",
    "garden": "bahce",
    "streetfood": "sokak-lezzeti",
    "railway": "tren",
    "railroad": "tren",
    "tracks": "tren",
    "track": "tren",
    "locomotive": "tren",
    "train": "tren",
    "market": "pazar-yeri",
    "boat-tour": "tekne",
    "rowing": "tekne",
    "rice-field": "pirinc-tarlasi",
}

DESTINATION_PHRASES = {
    "hanoi-old-quarter": "hanoi-old-quarter",
    "halong-bay": "halong-bay",
    "ha-long-bay": "halong-bay",
    "trang-an": "trang-an",
    "hoa-lu": "hoa-lu",
    "ho-chi-minh-city": "saygon",
    "ho-chi-minh": "saygon",
    "saigon": "saygon",
    "hanoi": "hanoi",
    "vietnam": "vietnam",
}

# Bilinen destinasyonlar için sabit koordinatlar.
# Kural:
# - Spesifik destinasyon adı tespit edilirse (örn. Batum Botanik Bahçesi) onun koordinatı yazılır.
# - Spesifik tespit yoksa ve ad/slug içinde "batum" geçiyorsa Batum merkez koordinatı fallback olarak yazılır.
DESTINATION_COORDINATES = {
    "batum-botanik-bahcesi": (41.6946, 41.7089),
    "batumi-botanical-garden": (41.6946, 41.7089),
    "batum": (41.6168, 41.6367),
    "batumi": (41.6168, 41.6367),
}

SCENE_PHRASES = {
    "train-street": "train-street",
    "narrow-street": "sokak",
    "street-market": "pazar-yeri",
    "floating-market": "pazar-yeri",
    "boat-tour": "tekne",
    "railway": "tren",
    "train": "tren",
    "bay": "korfezi",
    "market": "pazar-yeri",
}

VISION_SCENE_REMAP = {
    "boat": "tekne",
    "ship": "tekne",
    "watercraft": "tekne",
    "sea": "deniz",
    "ocean": "deniz",
    "bay": "korfezi",
    "beach": "sahil",
    "coast": "kiyi",
    "river": "nehir",
    "lake": "gol",
    "mountain": "dag",
    "forest": "orman",
    "market": "pazar-yeri",
    "street": "sokak",
    "train": "tren",
    "railway": "tren",
    "railroad": "tren",
    "bridge": "kopru",
    "temple": "tapinak",
    "pagoda": "pagoda",
    "palace": "saray",
    "castle": "kale",
    "garden": "bahce",
    "landscape": "manzara",
    "sunset": "gunbatimi",
    "sunrise": "gundogumu",
}


def slugify(value: str) -> str:
    # Büyük harf Türkçe karakterleri ÖNCE dönüştür (İ.lower() → i̇ problemi)
    text = str(value or "").strip()
    text = (
        text.replace("İ", "I")
        .replace("Ş", "S")
        .replace("Ç", "C")
        .replace("Ğ", "G")
        .replace("Ü", "U")
        .replace("Ö", "O")
    )
    text = text.lower()
    text = (
        text.replace("ş", "s")
        .replace("ç", "c")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ı", "i")
    )
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def is_good_slug(stem: str) -> bool:
    slug = slugify(stem)
    if not slug or len(slug) < 8:
        return False
    tokens = [token for token in slug.split("-") if token]
    if len(tokens) < 2:
        return False
    if any(token in FORBIDDEN_FALLBACK_TOKENS for token in tokens):
        return False
    if any(token in BAD_SLUG_TOKENS for token in tokens):
        return False
    if sum(ch.isdigit() for ch in slug) > max(3, len(slug) // 3):
        return False
    return True


def _clean_tokens(value: str) -> list[str]:
    slug = slugify(value)
    return [token for token in slug.split("-") if token]


def _extract_compound_locations(text: str) -> list[str]:
    slug = slugify(text)
    compounds: list[str] = []
    for needle, replacement in DESTINATION_PHRASES.items():
        if needle in slug and replacement not in compounds:
            compounds.append(replacement)
    return compounds


def _extract_scene_phrases(text: str) -> list[str]:
    slug = slugify(text)
    phrases: list[str] = []
    for needle, replacement in SCENE_PHRASES.items():
        if needle in slug and replacement not in phrases:
            phrases.append(replacement)
    return phrases


def read_embedded_source_metadata(path: str) -> Dict:
    source_path = Path(path)
    if not source_path.exists() or not shutil.which("exiftool"):
        return {}
    cmd = [
        "exiftool",
        "-json",
        "-Subject",
        "-Keywords",
        "-Description",
        "-Caption-Abstract",
        "-Title",
        "-ObjectName",
        "-Headline",
        "-Country",
        "-Country-PrimaryLocationName",
        "-City",
        str(source_path),
    ]
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        payload = json.loads(result.stdout or "[]")
        if not payload:
            return {}
        data = payload[0]
    except Exception:
        return {}

    raw_keywords = data.get("Subject") or data.get("Keywords") or []
    if isinstance(raw_keywords, str):
        raw_keywords = [item.strip() for item in raw_keywords.split(",")]
    keywords = [str(item).strip() for item in raw_keywords if str(item).strip()]
    location_parts = [
        str(data.get("City") or "").strip(),
        str(data.get("Country-PrimaryLocationName") or "").strip(),
        str(data.get("Country") or "").strip(),
    ]
    return {
        "title": str(data.get("Title") or data.get("ObjectName") or data.get("Headline") or "").strip(),
        "description": str(data.get("Description") or data.get("Caption-Abstract") or "").strip(),
        "keywords": keywords,
        "location": " ".join(part for part in location_parts if part).strip(),
    }


def _extract_destination_tokens(post_context: Dict) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for source in (post_context.get("slug", ""),):
        for token in _clean_tokens(source):
            if token in BAD_SLUG_TOKENS or token in GENERIC_POST_TOKENS:
                continue
            if token.isdigit():
                continue
            if token in seen:
                continue
            seen.add(token)
            tokens.append(token)
            if len(tokens) >= 2:
                return tokens
    return tokens


def _extract_path_destination_tokens(original_path: str) -> list[str]:
    path = Path(original_path)
    parts = [slugify(part) for part in path.parts]
    tokens: list[str] = []
    seen: set[str] = set()
    for part in parts:
        if not part:
            continue
        for token in part.split("-"):
            if (
                not token
                or token in BAD_SLUG_TOKENS
                or token in GENERIC_POST_TOKENS
                or token in GENERIC_SCENE_TOKENS
                or token in GENERIC_SOURCE_TOKENS
                or token.isdigit()
            ):
                continue
            if token in seen:
                continue
            seen.add(token)
            tokens.append(token)
            if len(tokens) >= 2:
                return tokens
    return tokens


def _extract_source_destination_tokens(source_metadata: Dict) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    description_text = str(source_metadata.get("description", ""))
    joined_text = description_text
    for token in _extract_compound_locations(joined_text):
        if any(token in existing or existing in token for existing in seen):
            continue
        if token not in seen:
            seen.add(token)
            tokens.append(token)
        if len(tokens) >= 2:
            return tokens
    for source in (description_text,):
        for token in _clean_tokens(source):
            if token in BAD_SLUG_TOKENS or token in GENERIC_POST_TOKENS or token in GENERIC_SCENE_TOKENS or token in GENERIC_SOURCE_TOKENS:
                continue
            if token.isdigit():
                continue
            if any(token in existing or existing in token for existing in seen):
                continue
            if token in seen:
                continue
            seen.add(token)
            tokens.append(token)
            if len(tokens) >= 2:
                return tokens
    return tokens


def _extract_source_destination_variants(source_metadata: Dict) -> list[str]:
    description_text = str(source_metadata.get("description", ""))
    variants: list[str] = []
    seen: set[str] = set()

    for token in _extract_compound_locations(description_text):
        if token not in seen:
            seen.add(token)
            variants.append(token)

    for token in _extract_source_destination_tokens(source_metadata):
        if token not in seen:
            seen.add(token)
            variants.append(token)

    return _cleanup_destination_tokens(variants)


def _normalize_scene_token(token: str) -> str:
    token = slugify(token)
    if not token:
        return ""
    return SCENE_REMAP.get(token, token)


def _extract_scene_tokens(metadata: Dict, destination_tokens: list[str]) -> list[str]:
    sources: list[str] = []
    source_metadata = metadata.get("_source_embedded", {})
    if isinstance(source_metadata, dict):
        sources.append(source_metadata.get("description", ""))
    keywords = metadata.get("keywords", [])
    if isinstance(keywords, list):
        sources.extend(str(item) for item in keywords[:6])
    sources.extend([metadata.get("title", ""), metadata.get("alt", "")])

    tokens: list[str] = []
    seen: set[str] = set(destination_tokens)
    for source in sources:
        for phrase in _extract_scene_phrases(str(source)):
            if any(phrase in existing or existing in phrase for existing in seen):
                continue
            if phrase in seen:
                continue
            seen.add(phrase)
            tokens.append(phrase)
            if len(tokens) >= 2:
                return tokens
        for raw in _clean_tokens(source):
            token = _normalize_scene_token(raw)
            if not token:
                continue
            if token in BAD_SLUG_TOKENS or token in GENERIC_POST_TOKENS or token in GENERIC_SCENE_TOKENS or token in GENERIC_SOURCE_TOKENS:
                continue
            if token.isdigit():
                continue
            if token in {"vietnam", "hanoi", "saygon", "halong", "halong-bay", "hoa-lu", "trang-an"}:
                continue
            if any(token in existing or existing in token for existing in seen):
                continue
            if token in seen:
                continue
            seen.add(token)
            tokens.append(token)
            if len(tokens) >= 2:
                return tokens
    return tokens


def _extract_vision_scene_tokens(metadata: Dict, destination_tokens: list[str]) -> list[str]:
    hints = metadata.get("_vision_hints", {})
    if not isinstance(hints, dict):
        return []
    labels = hints.get("labels", [])
    seen: set[str] = set(destination_tokens)
    tokens: list[str] = []
    for item in labels[:8]:
        raw = ""
        if isinstance(item, dict):
            raw = str(item.get("description", ""))
        else:
            raw = str(item)
        token = slugify(raw)
        if not token:
            continue
        token = VISION_SCENE_REMAP.get(token, token)
        if token in BAD_SLUG_TOKENS or token in GENERIC_POST_TOKENS or token in GENERIC_SCENE_TOKENS or token in GENERIC_SOURCE_TOKENS:
            continue
        if token in {"vietnam", "hanoi", "saygon", "halong", "halong-bay", "hoa-lu", "trang-an"}:
            continue
        if any(token in existing or existing in token for existing in seen):
            continue
        seen.add(token)
        tokens.append(token)
        if len(tokens) >= 2:
            break
    return tokens


def _cleanup_destination_tokens(tokens: list[str]) -> list[str]:
    if len(tokens) > 1 and "vietnam" in tokens:
        tokens = [token for token in tokens if token != "vietnam"]
    return tokens[:2]


def _cleanup_scene_tokens(tokens: list[str]) -> list[str]:
    if any("train-street" == token for token in tokens):
        tokens = [token for token in tokens if token != "tren"]
        tokens = [token for token in tokens if token != "sokak"]
    if any("pazar-yeri" == token for token in tokens):
        tokens = [token for token in tokens if token != "pazar"]
    return tokens[:2]


def _slug_fallback_variants(post_context: Dict, destination_tokens: list[str], scene_tokens: list[str]) -> list[str]:
    raw_slug_tokens = [
        token
        for token in _clean_tokens(post_context.get("slug", ""))
        if token not in BAD_SLUG_TOKENS and not token.isdigit()
    ]
    slug_tokens = raw_slug_tokens[:4] or destination_tokens[:]

    variants: list[list[str]] = []
    if slug_tokens:
        variants.append(slug_tokens[:4])
    if destination_tokens and slug_tokens:
        variants.append((destination_tokens[:1] + slug_tokens[:3])[:4])
        variants.append((slug_tokens[:2] + destination_tokens[:1])[:4])
    if destination_tokens:
        variants.append(destination_tokens[:3])
        variants.append((destination_tokens[:2] + ["manzara"])[:4])
        variants.append((destination_tokens[:2] + ["atmosfer"])[:4])
        variants.append((destination_tokens[:2] + ["detay"])[:4])
    if destination_tokens and scene_tokens:
        variants.append((destination_tokens[:2] + scene_tokens[:1])[:4])
        variants.append((scene_tokens[:1] + destination_tokens[:2])[:4])

    seen: set[str] = set()
    cleaned: list[str] = []
    for variant in variants:
        tokens = [token for token in variant if token]
        if len(tokens) < 2:
            continue
        if any(token in FORBIDDEN_FALLBACK_TOKENS for token in tokens):
            continue
        slug = "-".join(tokens)
        if slug in seen:
            continue
        seen.add(slug)
        cleaned.append(slug)
    return cleaned


def build_publish_slug(metadata: Dict, post_context: Dict | None, original_path: str) -> str:
    post_context = post_context or {}
    original_stem = Path(original_path).stem.replace("_yo", "")
    source_metadata = metadata.get("_source_embedded")
    if not isinstance(source_metadata, dict):
        source_metadata = read_embedded_source_metadata(original_path)
        if source_metadata:
            metadata["_source_embedded"] = source_metadata
    if is_good_slug(original_stem):
        return slugify(original_stem)

    destination_tokens = _cleanup_destination_tokens(
        _extract_source_destination_tokens(source_metadata or {})
        or _extract_destination_tokens(post_context)
        or _extract_path_destination_tokens(original_path)
    )
    scene_tokens = _cleanup_scene_tokens(_extract_scene_tokens(metadata, destination_tokens))
    if not scene_tokens:
        scene_tokens = _cleanup_scene_tokens(_extract_vision_scene_tokens(metadata, destination_tokens))

    if not scene_tokens:
        original_tokens = [
            token
            for token in _clean_tokens(original_stem)
            if token not in BAD_SLUG_TOKENS and token not in GENERIC_POST_TOKENS and not token.isdigit()
        ]
        scene_tokens = original_tokens[:2]

    if not destination_tokens and not scene_tokens:
        return "seyahat-kare"
    if not destination_tokens:
        return "-".join(scene_tokens[:3]) or "seyahat-kare"
    if not scene_tokens:
        variants = _slug_fallback_variants(post_context, destination_tokens, scene_tokens)
        if variants:
            return variants[0]
        return "-".join((destination_tokens + ["sahne"])[:4])
    raw = "-".join((destination_tokens + scene_tokens)[:5])
    deduped: list[str] = []
    for token in raw.split("-"):
        if token and token not in deduped:
            deduped.append(token)
    return "-".join(deduped[:5]) or "seyahat-kare"


def build_publish_slug_candidates(metadata: Dict, post_context: Dict | None, original_path: str) -> list[str]:
    post_context = post_context or {}
    primary = build_publish_slug(metadata, post_context, original_path)
    candidates: list[str] = [primary]
    source_metadata = metadata.get("_source_embedded")
    if not isinstance(source_metadata, dict):
        source_metadata = read_embedded_source_metadata(original_path)
        if source_metadata:
            metadata["_source_embedded"] = source_metadata
    verified_locations = _cleanup_destination_tokens(
        _extract_source_destination_tokens(source_metadata or {})
    )
    verified_location_variants = _extract_source_destination_variants(source_metadata or {})
    scene_tokens = _cleanup_scene_tokens(_extract_scene_tokens(metadata, verified_locations))
    if not scene_tokens:
        scene_tokens = _cleanup_scene_tokens(_extract_vision_scene_tokens(metadata, verified_locations))
    slug_base = slugify(post_context.get("slug", ""))

    if primary == slug_base or primary.startswith(slug_base + "-"):
        for location in verified_location_variants:
            for variant in (
                f"{slug_base}-{location}" if slug_base else location,
                f"{location}-vietnam" if location != "vietnam" else "",
                f"vietnam-{location}" if location != "vietnam" else "",
            ):
                clean = slugify(variant)
                if clean and clean not in candidates:
                    candidates.append(clean)
        for scene in scene_tokens:
            for variant in (
                f"{slug_base}-{scene}" if slug_base else scene,
                f"vietnam-{scene}" if "vietnam" in verified_locations else "",
            ):
                clean = slugify(variant)
                if clean and clean not in candidates:
                    candidates.append(clean)

    if primary in {"gorsel", "seyahat-manzara"}:
        for location in verified_location_variants:
            clean = slugify(location)
            if clean and clean not in candidates:
                candidates.append(clean)
    cleaned: list[str] = []
    for item in candidates:
        tokens = [token for token in item.split("-") if token]
        if any(token in FORBIDDEN_FALLBACK_TOKENS for token in tokens):
            continue
        cleaned.append(item)
    if cleaned:
        return cleaned
    destination_hint = _cleanup_destination_tokens(
        _extract_source_destination_tokens(source_metadata or {})
        or _extract_destination_tokens(post_context)
        or _extract_path_destination_tokens(original_path)
    )
    if destination_hint:
        return ["-".join((destination_hint + ["detay"])[:4])]
    return ["seyahat-kare"]


def ensure_unique_slug(slug: str, used: set[str]) -> str:
    clean = slugify(slug) or "seyahat-kare"
    if clean not in used:
        return clean
    word_suffixes = [
        "detay",
        "atmosfer",
        "kare",
        "mimari",
        "doga",
        "yol",
        "sahne",
        "rota",
        "sokak",
        "manzara",
        "panorama",
        "detay-kare",
    ]
    for suffix in word_suffixes:
        candidate = f"{clean}-{suffix}"
        if candidate not in used:
            return candidate
    raise ValueError(f"Non-numeric unique slug could not be produced for '{clean}'")


def ensure_publish_path(directory: Path, slug: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    existing_stems = {
        path.stem
        for path in directory.glob("*.webp")
    }
    resolved_slug = ensure_unique_slug(slug, existing_stems)
    return directory / f"{resolved_slug}.webp"


def _flatten_text_values(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        parts: list[str] = []
        for item in value:
            parts.extend(_flatten_text_values(item))
        return parts
    if isinstance(value, dict):
        parts: list[str] = []
        for item in value.values():
            parts.extend(_flatten_text_values(item))
        return parts
    return []


def _resolve_gps_coordinates(path: str, metadata: Dict) -> tuple[float, float] | None:
    candidates: list[str] = [Path(path).stem]
    for key in (
        "title",
        "alt",
        "caption",
        "description",
        "slug",
        "keywords",
        "location_tokens",
        "verified_locations",
        "verified_location_variants",
    ):
        candidates.extend(_flatten_text_values(metadata.get(key)))

    slug_haystack = slugify(" ".join(part for part in candidates if part))
    if not slug_haystack:
        return None

    # Önce spesifik eşleşmeler
    for needle in ("batum-botanik-bahcesi", "batumi-botanical-garden"):
        if needle in slug_haystack:
            return DESTINATION_COORDINATES[needle]

    # Sonra genel Batum fallback
    if "batum" in slug_haystack or "batumi" in slug_haystack:
        return DESTINATION_COORDINATES["batum"]

    return None


def embed_metadata(path: str, metadata: Dict) -> bool:
    if not shutil.which("exiftool"):
        return False

    keywords = metadata.get("keywords", [])
    if isinstance(keywords, list):
        keyword_value = ",".join(str(item).strip() for item in keywords if str(item).strip())
    else:
        keyword_value = ""

    cmd = [
        "exiftool",
        "-overwrite_original",
        f"-XMP-dc:Title={metadata.get('title', '')}",
        f"-XMP-dc:Description={metadata.get('description', '')}",
        f"-XMP-dc:Subject={keyword_value}",
        f"-XMP-photoshop:Headline={metadata.get('title', '')}",
        f"-XMP-iptcExt:AltTextAccessibility={metadata.get('alt', '')}",
        f"-IPTC:ObjectName={metadata.get('title', '')}",
        f"-IPTC:Caption-Abstract={metadata.get('caption', '')}",
        f"-IPTC:Keywords={keyword_value}",
    ]

    gps_coords = _resolve_gps_coordinates(path, metadata)
    if gps_coords:
        lat, lon = gps_coords
        cmd.extend(
            [
                f"-GPSLatitude={abs(lat)}",
                f"-GPSLongitude={abs(lon)}",
                f"-GPSLatitudeRef={'N' if lat >= 0 else 'S'}",
                f"-GPSLongitudeRef={'E' if lon >= 0 else 'W'}",
                f"-XMP-exif:GPSLatitude={lat}",
                f"-XMP-exif:GPSLongitude={lon}",
            ]
        )

    cmd.append(path)
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False
