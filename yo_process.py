#!/usr/bin/env python3
"""
yo_process.py — Manuel resim işleme
Kullanım: python3 yo_process.py "IMG_4106-1"
"""

import sys
import os
import re
import warnings
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from settings import DEFAULT_OUTPUT_DIR, get_vil_dir, load_project_env

load_project_env()

warnings.filterwarnings("ignore")

# ── Sabitler ────────────────────────────────────────────────────────────────
VIL_DIR   = get_vil_dir()
OUT_DIR   = DEFAULT_OUTPUT_DIR
LUT_PATH  = Path(__file__).parent / "luts" / "VELVIA_01.cube"
TARGET_W  = 1200


# ── LUT ─────────────────────────────────────────────────────────────────────
def load_lut():
    import colour
    return colour.io.read_LUT(str(LUT_PATH))


def apply_lut(img_array: np.ndarray, lut) -> np.ndarray:
    graded = lut.apply(img_array)
    return np.clip(graded, 0, 1)


# ── Görüntü işleme ───────────────────────────────────────────────────────────
def process(img: Image.Image) -> Image.Image:
    """Resize → Velvia LUT → Sharpness"""
    if img.mode != "RGB":
        img = img.convert("RGB")

    img = img.resize((TARGET_W, int(TARGET_W * img.height / img.width)),
                     Image.Resampling.LANCZOS)

    arr = np.array(img, dtype=np.float32) / 255.0

    # Adaptive brightness: çok karanlık veya çok parlak ise düzelt
    brightness = float(np.mean(arr))
    if brightness < 0.30:
        arr = np.power(arr, 0.88)           # lift
    elif brightness > 0.72:
        arr = np.power(arr, 1.10)           # pull down

    # Velvia LUT
    lut = load_lut()
    arr = apply_lut(arr, lut)

    out = Image.fromarray((arr * 255).astype(np.uint8))

    # Sharpness
    out = out.filter(ImageFilter.UnsharpMask(radius=1.0, percent=10, threshold=2))
    return out


# ── Metadata ─────────────────────────────────────────────────────────────────
def get_post_info(post_id: int, site: str = "yoldaolmak") -> dict:
    """WP REST API'den post title ve slug'ı oku"""
    import requests, base64
    from yo_wp_uploader import YOWordPressUploader
    site_cfg = YOWordPressUploader.SITE_ENDPOINTS.get(site, {})
    base_url = site_cfg.get("url", "")
    user     = site_cfg.get("user", "")
    password = site_cfg.get("password", "")

    creds = base64.b64encode(f"{user}:{password}".encode()).decode()
    try:
        r = requests.get(
            f"{base_url}/wp-json/wp/v2/posts/{post_id}",
            headers={"Authorization": f"Basic {creds}"},
            timeout=10
        )
        data = r.json()
        import html as _html
        title   = _html.unescape(data.get("title",   {}).get("rendered", ""))
        slug    = data.get("slug", "")
        excerpt = _html.unescape(
            re.sub(r'<[^>]+>', '', data.get("excerpt", {}).get("rendered", ""))
        ).strip()
        # İlk cümleyi al
        first_sentence = re.split(r'(?<=[.!?])\s', excerpt)[0] if excerpt else ""
        content_raw  = data.get("content", {}).get("rendered", "")
        # Style/script bloklarını önce temizle
        content_clean = re.sub(r'<style[^>]*>.*?</style>', ' ', content_raw, flags=re.S | re.I)
        content_clean = re.sub(r'<script[^>]*>.*?</script>', ' ', content_clean, flags=re.S | re.I)
        content_text  = re.sub(r'<[^>]+>', ' ', content_clean)
        content_text  = re.sub(r'\s+', ' ', content_text).strip()[:4000]
        return {
            "title": title, "slug": slug, "excerpt": excerpt,
            "first_sentence": first_sentence, "content": content_text,
        }
    except Exception:
        return {}


# ── İçerik detayı çıkarma ────────────────────────────────────────────────────

_TR_CITIES = [
    "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Konya",
    "Gaziantep", "Mersin", "Diyarbakır", "Kayseri", "Eskişehir", "Trabzon",
    "Samsun", "Malatya", "Denizli", "Erzurum", "Van", "Balıkesir", "Muğla",
    "Kahramanmaraş", "Hatay", "Ordu", "Rize", "Artvin", "Nevşehir", "Niğde",
    "Karaman", "Aksaray", "Kapadokya", "Çanakkale", "Edirne", "Tekirdağ",
    "Bolu", "Kastamonu", "Sinop", "Amasya", "Giresun", "Aydın", "Manisa",
    "Afyon", "Kütahya", "Uşak", "Isparta", "Burdur", "Mardin", "Batman",
    "Erzincan", "Kars", "Çorum", "Tokat", "Sivas", "Yozgat", "Zonguldak",
    "Bartın", "Karabük", "Düzce", "Yalova", "Kocaeli", "Sakarya",
    "Elazığ", "Adıyaman", "Şanlıurfa", "Kilis", "Osmaniye",
]

# (regex_pattern, display_label)
_FEATURE_PATTERNS = [
    (r'yeralt[ıi]\s*göl[üu]|aynalı\s*göl',   'yeraltı gölü'),
    (r'sarkıt',                                 'sarkıt'),
    (r'dikit',                                  'dikit'),
    (r'şelale|çağlayan',                        'şelale'),
    (r'plaj|kumsal',                            'plaj'),
    (r'\bkoy\b|körfez',                         'koy'),
    (r'\bgöl\b',                                'göl'),
    (r'nehir|ırmak|\bçay\b',                    'nehir'),
    (r'vadi|kanyon',                            'vadi'),
    (r'orman',                                  'orman'),
    (r'\bdağ\b|\btepe\b|\bzirve\b',             'dağ'),
    (r'\bkale\b|\bhisar\b',                     'kale'),
    (r'antik\s*kent|harabe|kalıntı',            'antik kalıntı'),
    (r'\bdeniz\b(?!\s*seviyesi)|\bsahil\b',      'deniz'),
    (r'pazar|çarşı',                            'çarşı'),
    (r'liman|iskele',                           'liman'),
    (r'mağara',                                 'mağara'),
]


def extract_content_details(content: str) -> dict:
    """Post içeriğinden şehir, ilçe ve fiziksel özellik çıkar."""
    result = {"city": "", "district": "", "features": []}
    if not content:
        return result

    def _norm(s: str) -> str:
        return s.lower().translate(str.maketrans("şçğüöıİŞÇĞÜÖ", "scguoiISCGUO"))

    norm_content = _norm(content)

    # Şehir — uzundan kısaya, tam kelime eşleşmesi (\b Unicode-aware)
    for city in sorted(_TR_CITIES, key=len, reverse=True):
        city_norm = _norm(city)
        if re.search(r'\b' + re.escape(city_norm) + r'\b', norm_content):
            result["city"] = city
            break

    # İlçe: "X ilçe" kalıbı
    m = re.search(r'(\w+)\s+ilçe', content, re.IGNORECASE)
    if m:
        result["district"] = m.group(1)

    # Fiziksel özellikler — daha spesifik olanlar önce; kapsayan bulununca genel atla
    features = []
    found_labels = set()
    for pattern, label in _FEATURE_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            # "göl" varken "yeraltı gölü" zaten eklendiyse "göl" tekrarını atla
            skip = False
            for already in found_labels:
                if label in already or already in label:
                    skip = True
                    break
            if not skip:
                features.append(label)
                found_labels.add(label)
        if len(features) == 3:
            break
    result["features"] = features

    return result


# ── Fotoğraf dosya adı üretimi ───────────────────────────────────────────────

# CV label → (sub_type, descriptor)
# sub_type: "water" | "formation" | "view" | "info" | "general"
_CV_MAP = {
    # Formasyon (mağara oluşumları)
    "stalactite":           ("formation", "sarkit"),
    "stalactites":          ("formation", "sarkit"),
    "stalagmite":           ("formation", "dikit"),
    "stalagmites":          ("formation", "dikit"),
    "speleothem":           ("formation", "sarkit-dikit"),
    "speleothems":          ("formation", "sarkit-dikit"),
    "underground":          ("formation", "ici"),
    "interior":             ("formation", "ici"),
    "inside":               ("formation", "ici"),
    "cave":                 ("formation", "ici"),
    "grotto":               ("formation", "ici"),
    "cavern":               ("formation", "ici"),
    # Su / göl
    "lake":                 ("water",     "golu"),
    "lagoon":               ("water",     "golu"),
    "reflection":           ("water",     "golu"),
    "blue":                 ("water",     "ici"),
    "water":                ("water",     "golu"),
    # Manzara / dış görünüm
    "waterfall":            ("view",      "selalesi"),
    "beach":                ("view",      "plaji"),
    "coast":                ("view",      "sahili"),
    "glacier":              ("view",      "buzulu"),
    "mountain":             ("view",      "manzarasi"),
    "panorama":             ("view",      "manzarasi"),
    "aerial":               ("view",      "manzarasi"),
    "sunrise":              ("view",      "gunbatimi"),
    "sunset":               ("view",      "gunbatimi"),
    "forest":               ("view",      "ormani"),
    "canyon":               ("view",      "kanyonu"),
    "valley":               ("view",      "vadisi"),
    "castle":               ("view",      "kalesi"),
    "ruins":                ("view",      "kalintilari"),
    "temple":               ("view",      "tapinagi"),
    "mosque":               ("view",      "camii"),
    "market":               ("view",      "pazari"),
    "bazaar":               ("view",      "carsisi"),
    "harbor":               ("view",      "limani"),
    "river":                ("view",      "nehri"),
    # Bilgi / yol tarifi
    "road":                 ("info",      "nasil-gidilir"),
    "path":                 ("info",      "nasil-gidilir"),
    "trail":                ("info",      "nasil-gidilir"),
    "sign":                 ("info",      "nerede"),
    "signage":              ("info",      "nerede"),
    "map":                  ("info",      "nerede"),
    "parking":              ("info",      "nasil-gidilir"),
    "entrance":             ("info",      "giris"),
    "gate":                 ("info",      "giris"),
    "ticket":               ("info",      "bilgi"),
    "building":             ("info",      "nerede"),
}

# İçerik özelliği → descriptor (CV yoksa fallback)
_FEATURE_TO_DESC = {
    "yeraltı gölü": "ici",
    "göl":          "golu",
    "sarkıt":       "sarkit",
    "dikit":        "dikit",
    "şelale":       "selalesi",
    "plaj":         "plaji",
    "koy":          "koyu",
    "nehir":        "nehri",
    "vadi":         "vadisi",
    "dağ":          "manzarasi",
    "kale":         "kalesi",
    "deniz":        "sahili",
    "çarşı":        "carsisi",
    "liman":        "limani",
}

# Aynı descriptor geldiğinde sıradaki varyant
_DESCRIPTOR_VARIANTS = {
    "ici":        ["ici", "ic-gorunum", "ic-detay", "ic-gecit"],
    "ic-gorunum": ["ic-gorunum", "ici", "ic-detay"],
    "sarkit":     ["sarkit", "sarkit-dikit", "olusum"],
    "dikit":      ["dikit", "sarkit-dikit", "olusum"],
    "sarkit-dikit":["sarkit-dikit", "sarkit", "dikit", "olusum"],
    "golu":       ["golu", "ic-gol", "ayna-gol"],
    "manzarasi":  ["manzarasi", "panorama", "gorunum"],
}


def extract_paren_name(title: str) -> str:
    """Başlıktaki parantez içi alternatif adı slug olarak döner.
    "Aynalıgöl (Gilindire) Mağarası" → "gilindire"
    """
    m = re.search(r'\(([^)]+)\)', title)
    return slugify(m.group(1).strip()) if m else ""


def photo_file_slug(dest_slug: str, post_title: str,
                    cv_labels: list, features: list,
                    used_slugs: set = None) -> str:
    """Fotoğraf içeriğine göre benzersiz, anlamlı dosya slug'u üret.

    Mantık:
      - Parantezdeki alt adı çıkar (Gilindire, Aynalıgöl gibi)
      - CV sub_type → hangi location component kullanılacak:
          formation → alt_name (gilindire)
          water     → dest_first kelimesi (aynaligol)
          view/info → dest_slug
      - Descriptor → suffix
      - Daha önce kullanıldıysa variant listesinden sıradakine geç
    """
    if used_slugs is None:
        used_slugs = set()

    alt_name  = extract_paren_name(post_title)           # "gilindire"
    dest_first = dest_slug.split("-")[0]                  # "aynaligol"
    cv_lower  = [l.lower() for l in cv_labels]

    # CV label'lardan en spesifik eşleşmeyi bul
    # Önce formation/water (spesifik), sonra view, sonra general
    sub_type   = ""
    descriptor = ""
    for label in cv_lower:
        if label in _CV_MAP:
            sub_type, descriptor = _CV_MAP[label]
            # Formation veya water ise dur (en anlamlı)
            if sub_type in ("formation", "water"):
                break

    # CV yoksa içerik özelliklerinden fallback
    if not descriptor:
        for feat in features:
            if feat in _FEATURE_TO_DESC:
                descriptor = _FEATURE_TO_DESC[feat]
                sub_type   = "formation" if "gölü" in feat else "view"
                break

    # Location component
    if sub_type == "water":
        loc = dest_first                           # aynaligol
    elif sub_type == "formation" and alt_name:
        loc = alt_name                             # gilindire
    elif sub_type == "info":
        loc = dest_slug                            # full slug
    else:
        loc = dest_slug                            # full slug

    # Birleştir
    base = f"{loc}-{descriptor}" if descriptor else loc

    # Çakışma varsa variant dene
    if base in used_slugs:
        variants = _DESCRIPTOR_VARIANTS.get(descriptor, [descriptor])
        for variant in variants:
            candidate = f"{loc}-{variant}"
            if candidate not in used_slugs:
                base = candidate
                break

    return base


def cv_to_visual_desc(cv_labels: list) -> tuple:
    """CV labels → (Türkçe görsel açıklama, is_interior)

    Returns:
        desc: "sarkıt ve dikit oluşumları" / "deniz ve kaya manzarası" / ...
        is_interior: True = mağara/iç mekan içinde çekilmiş
    """
    cv_lower = {l.lower() for l in cv_labels}

    has = lambda *keys: any(k in cv_lower for k in keys)

    stalactite  = has("stalactite", "stalactites")
    stalagmite  = has("stalagmite", "stalagmites")
    speleothem  = has("speleothem", "speleothems")
    cave        = has("cave", "grotto", "cavern", "underground", "interior", "inside")
    lake        = has("lake", "lagoon", "lakes")
    water_blue  = has("blue", "water", "reflection", "turquoise", "aqua")
    sea_coast   = has("coast", "headland", "sea", "ocean", "cliff", "terrain")
    mountain    = has("mountain", "peak", "summit", "ridge", "panorama", "aerial")
    waterfall   = has("waterfall", "cascade")
    beach       = has("beach", "sand", "shore")
    rock_out    = has("rock") and not cave and not underground
    forest      = has("forest", "tree", "vegetation", "jungle")
    ruins       = has("ruins", "castle", "ancient", "temple", "mosque")
    market      = has("market", "bazaar")
    road        = has("road", "path", "trail", "street")

    is_interior = cave or stalactite or stalagmite or speleothem

    parts = []

    # Formasyon detayları (en spesifik önce)
    if stalactite and stalagmite:
        parts.append("sarkıt ve dikit oluşumları")
    elif stalactite:
        parts.append("sarkıt oluşumları")
    elif stalagmite:
        parts.append("dikit oluşumları")
    elif speleothem:
        parts.append("sarkıt dikit oluşumları")

    # Göl / su
    if lake or (water_blue and is_interior):
        parts.append("yeraltı gölü")
    elif water_blue and not is_interior:
        parts.append("su yansıması")

    # Genel iç görünüm (formasyon yoksa)
    if not parts and is_interior:
        parts.append("iç görünüm")

    # Dış manzara
    if not parts:
        if waterfall:
            parts.append("şelale")
        elif beach:
            parts.append("plaj")
        elif sea_coast and rock_out:
            parts.append("deniz ve kaya manzarası")
        elif sea_coast:
            parts.append("kıyı manzarası")
        elif mountain:
            parts.append("dağ manzarası")
        elif forest:
            parts.append("orman manzarası")
        elif ruins:
            parts.append("tarihi kalıntılar")
        elif market:
            parts.append("pazar")
        elif road:
            parts.append("yol")

    desc = " ve ".join(parts) if parts else ""
    return desc, is_interior


# Renk, genel teknik terimler — SEO değeri yok
# Whitelist: sadece bunlar anlamlı label olarak kabul edilir
_MEANINGFUL_LABELS = {
    "cave", "grotto", "cavern", "stalactite", "stalagmite",
    "waterfall", "river", "lake", "glacier",
    "mountain", "cliff", "valley", "canyon", "volcano",
    "beach", "bay", "cove", "lagoon",
    "forest", "jungle", "meadow", "desert",
    "castle", "ruins", "temple", "mosque", "church", "monastery",
    "market", "bazaar", "village",
    "boat", "ship", "harbor",
    "sunset", "sunrise",
}

def extract_destination(title: str, slug: str) -> tuple:
    """Title + slug'dan destinasyon adını ve slug'unu çıkar.

    Title formatları:
      "Aynalıgöl Mağarası: Gilindire'nin Gizli Hazinesi"   → "Aynalıgöl Mağarası"
      "Türkiye'nin En Güzeli: Aynalıgöl Mağarası"          → "Aynalıgöl Mağarası"
      "Kapadokya Rehberi – Göreme'de Ne Yapılır"            → "Kapadokya"
      "Gilindire Mağarası"                                   → "Gilindire Mağarası"

    Returns:
        (destination_display, destination_slug)
    """
    # Başlığı ayır: ":", "–", "-", "|"
    parts = re.split(r'\s*[:\–\|]\s*|\s+[-—]\s+', title)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) > 1:
        # Slug ile en çok örtüşen parçayı seç
        best = max(parts, key=lambda p: _slug_overlap(slugify(p), slug))
        # Eğer hiç örtüşme yoksa en kısa parçayı al (intro değil, destinasyon)
        if _slug_overlap(slugify(best), slug) == 0:
            best = min(parts, key=len)
    else:
        best = parts[0]

    return best, slugify(best)


def _slug_overlap(a: str, b: str) -> int:
    """İki slug arasındaki ortak karakter sayısı (prefix match)"""
    return sum(1 for ca, cb in zip(a, b) if ca == cb)


def smart_meta(post_slug: str, post_title: str, cv_labels: list,
               post_excerpt: str = "", content: str = "",
               used_slugs: set = None) -> dict:
    """Post title + slug + excerpt + content → SEO meta

    Hedef format:
      alt:         Aynalıgöl Gilindire Mağarası içindeki yer altı gölü ve sarkıt dikit oluşumları
      title:       Aynalıgöl Mağarası
      caption:     Mersin Aydıncık Aynalıgöl (Gilindire) Mağarası'nın içindeki berrak yer altı gölü
      description: (excerpt ilk cümle)
    """
    dest_display, dest_slug = extract_destination(post_title, post_slug)
    print(f"   Destinasyon: {dest_display} → {dest_slug}")

    details  = extract_content_details(content)
    city     = details["city"]
    district = details["district"]
    dest_lower = dest_display.lower()
    features = [f for f in details["features"] if f.lower() not in dest_lower]

    print(f"   Şehir: {city or '—'}  İlçe: {district or '—'}")

    # ── CV → görsel açıklama (fotoğrafa özel) ─────────────────────────────
    cv_desc, is_interior = cv_to_visual_desc(cv_labels)
    preposition = "içindeki" if is_interior else "çevresindeki"
    print(f"   CV görsel: {cv_desc or '—'}  ({'iç' if is_interior else 'dış'})")

    # ── ALT TEXT ──────────────────────────────────────────────────────────
    # CV varsa fotoğrafa özel; yoksa dest_display
    if cv_desc:
        alt = f"{dest_display} {preposition} {cv_desc}"
    else:
        alt = dest_display

    # ── TITLE ─────────────────────────────────────────────────────────────
    title = dest_display

    # ── CAPTION ───────────────────────────────────────────────────────────
    loc_parts = [p for p in [city, district] if p]
    if loc_parts and cv_desc:
        loc_str = " ".join(loc_parts)
        if dest_display[-1] in "aıouAIOU":
            poss = "'nın"
        else:
            poss = "'nin"
        caption = f"{loc_str} {dest_display}{poss} {preposition} {cv_desc}"
    elif loc_parts:
        caption = f"{' '.join(loc_parts)} {dest_display}"
    else:
        caption = alt

    # ── DESCRIPTION ───────────────────────────────────────────────────────
    description = post_excerpt[:300] if post_excerpt else f"{dest_display}."

    # ── SLUG (dosya adı) ──────────────────────────────────────────────────
    file_slug = photo_file_slug(dest_slug, post_title, cv_labels, features, used_slugs)
    print(f"   Dosya adı: {file_slug}")

    return {
        "alt":         alt[:125],
        "title":       title[:60],
        "caption":     caption[:200],
        "description": description[:300],
        "keywords":    [dest_slug],
        "slug":        file_slug,
    }


def generate_metadata(img_path: str, stem: str, location: str = "", post_id: int = None,
                      site: str = "yoldaolmak", used_slugs: set = None,
                      _post_info_cache: dict = None) -> dict:
    """IPTC → CV Vision → fallback öncelik sırası"""
    # 1. Post ID varsa WP'den destinasyon bilgisi al (cache)
    post_info = _post_info_cache if _post_info_cache is not None else {}
    if not post_info and post_id:
        post_info = get_post_info(post_id, site=site)

    # 2. IPTC/XMP metadata oku (Depositphotos ve stok fotoğraf kaynakları)
    iptc = read_iptc(img_path)
    cv_labels = []

    if iptc.get("keywords"):
        # IPTC keywords doğrudan CV label olarak kullan
        cv_labels = iptc["keywords"]
        print(f"   IPTC keywords: {cv_labels[:6]}")
    else:
        # 3. IPTC yoksa Cloud Vision (cache kontrol)
        cv_labels = _cv_cache_get(img_path)
        if cv_labels is not None:
            print(f"   CV labels (cache): {cv_labels[:5]}")
        else:
            api_key = os.environ.get("GOOGLE_CLOUD_VISION_KEY")
            if api_key:
                try:
                    from yo_cloud_vision import YOCloudVisionClient
                    client = YOCloudVisionClient(api_key=api_key)
                    analysis = client.analyze(img_path)
                    if "error" not in analysis:
                        cv_labels = [l["description"] for l in analysis.get("labels", [])]
                        _cv_cache_set(img_path, cv_labels)
                        print(f"   CV labels: {cv_labels[:5]}")
                except Exception:
                    pass
            if cv_labels is None:
                cv_labels = []

    # 4. Post bilgileri + labels → SEO meta
    if post_info.get("slug"):
        print(f"   Post: {post_info['title']}")
        # IPTC description varsa excerpt'e öncelik ver
        excerpt = iptc.get("description") or post_info.get("first_sentence", "")
        return smart_meta(
            post_slug=post_info["slug"],
            post_title=post_info["title"],
            post_excerpt=excerpt,
            cv_labels=cv_labels,
            content=post_info.get("content", ""),
            used_slugs=used_slugs,
        )

    # 4. Fallback: location veya dosya adından
    base = slugify(location) if location else slugify(re.sub(r'[_\-]+', ' ', stem))
    return {
        "alt":         base[:125],
        "title":       (location or stem).replace("-", " ").title()[:60],
        "caption":     (location or stem).replace("-", " ").title(),
        "description": f"{(location or stem).title()}. Profesyonel seyahat fotoğrafçılığı.",
        "keywords":    base.split("-"),
        "slug":        base,
    }


# ── CV cache ─────────────────────────────────────────────────────────────────
_CV_CACHE_FILE = Path(__file__).parent / ".cv_cache.json"

def _cv_cache_load() -> dict:
    try:
        import json as _j
        return _j.loads(_CV_CACHE_FILE.read_text()) if _CV_CACHE_FILE.exists() else {}
    except Exception:
        return {}

def _cv_cache_save(cache: dict):
    import json as _j
    _CV_CACHE_FILE.write_text(_j.dumps(cache, ensure_ascii=False))

def _cv_cache_key(img_path: str) -> str:
    """Dosya adı + boyut → cache key (path bağımsız)"""
    p = Path(img_path)
    return f"{p.name}:{p.stat().st_size}"

def _cv_cache_get(img_path: str):
    """Cache'de varsa label listesi döner, yoksa None."""
    cache = _cv_cache_load()
    return cache.get(_cv_cache_key(img_path))

def _cv_cache_set(img_path: str, labels: list):
    cache = _cv_cache_load()
    cache[_cv_cache_key(img_path)] = labels
    _cv_cache_save(cache)


def read_iptc(img_path: str) -> dict:
    """exiftool ile IPTC/XMP metadata oku.
    Returns: {keywords: [...], description: str, title: str}
    """
    import subprocess
    try:
        result = subprocess.run(
            ["exiftool", "-json", "-Subject", "-Description", "-Title",
             "-Keywords", "-Caption-Abstract", img_path],
            capture_output=True, text=True, timeout=10
        )
        import json as _json
        data = _json.loads(result.stdout)
        if not data:
            return {}
        d = data[0]

        # Keywords: Subject veya Keywords alanından
        raw_kw = d.get("Subject") or d.get("Keywords") or []
        if isinstance(raw_kw, str):
            raw_kw = [k.strip() for k in raw_kw.split(",")]
        keywords = [k.strip() for k in raw_kw if k.strip()]

        description = (d.get("Description") or d.get("Caption-Abstract") or "").strip()
        title       = (d.get("Title") or "").strip()

        return {"keywords": keywords, "description": description, "title": title}
    except Exception:
        return {}


def slugify(text: str) -> str:
    tr = str.maketrans("şçğüöıİŞÇĞÜÖ", "scguoiISCGUO")
    text = text.translate(tr).lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text[:60]


# ── Ana akış ─────────────────────────────────────────────────────────────────
def run(query: str, location: str = "", post_id: int = None, site: str = "yoldaolmak",
        used_slugs: set = None, _post_info_cache: dict = None, dry_run: bool = False):
    # VIL'de dosyayı bul
    query_lower = query.lower()
    candidates = sorted(
        [f for f in VIL_DIR.iterdir()
         if f.suffix.lower() in {'.jpg', '.jpeg', '.png'}
         and query_lower in f.stem.lower()],
        key=lambda p: p.stat().st_mtime, reverse=True
    )

    if not candidates:
        print(f"✗ '{query}' VIL klasöründe bulunamadı")
        sys.exit(1)

    src = candidates[0]
    print(f"📷 {src.name}")

    if dry_run:
        # ── DRY RUN: sadece meta göster, dosyaya dokunma ──────────────────
        if used_slugs is None:
            used_slugs = set()
        meta = generate_metadata(str(src), stem=src.stem, location=location, post_id=post_id,
                                 site=site, used_slugs=used_slugs, _post_info_cache=_post_info_cache)
        used_slugs.add(meta.get("slug", ""))
        new_name = (meta.get("slug") or slugify(meta.get("title", src.stem))) + ".webp"
        print(f"\n   [DRY RUN] Dosya adı : {new_name}")
        print(f"   [DRY RUN] Alt       : {meta.get('alt', '')}")
        print(f"   [DRY RUN] Caption   : {meta.get('caption', '')}")
        print(f"   [DRY RUN] Title     : {meta.get('title', '')}")
        print(f"   [DRY RUN] Desc      : {meta.get('description', '')[:80]}...")
        return Path(OUT_DIR / new_name), meta

    # İşle
    img = Image.open(src)
    print(f"   {img.width}×{img.height} → ", end="")
    img_out = process(img)
    print(f"{img_out.width}×{img_out.height}")

    # Metadata
    if used_slugs is None:
        used_slugs = set()
    meta = generate_metadata(str(src), stem=src.stem, location=location, post_id=post_id,
                             site=site, used_slugs=used_slugs, _post_info_cache=_post_info_cache)
    used_slugs.add(meta.get("slug", ""))

    # Yeni ad: meta'daki slug varsa onu kullan, yoksa title'dan üret
    new_name = (meta.get("slug") or slugify(meta.get("title", src.stem))) + ".webp"
    out_path = OUT_DIR / new_name

    # EXIF temizle & kaydet
    clean = Image.new(img_out.mode, img_out.size)
    clean.putdata(list(img_out.getdata()))
    clean.save(str(out_path), "WEBP", quality=85, method=6)

    # Eski sürümleri temizle
    dest_slug = (meta.get("keywords") or [""])[0]
    if dest_slug:
        for old in OUT_DIR.iterdir():
            if old == out_path:
                continue
            if old.suffix.lower() in {".webp", ".json"} and old.stem.startswith(dest_slug):
                old.unlink()
                print(f"   🗑  Silindi: {old.name}")

    size_kb = out_path.stat().st_size / 1024
    print(f"\n✅ {out_path.name}  ({size_kb:.0f} KB)")
    print(f"   Alt:   {meta.get('alt', '')}")
    print(f"   Title: {meta.get('title', '')}")

    return out_path, meta


def upload(img_path: Path, meta: dict, post_id: int, site: str = "yoldaolmak"):
    from yo_wp_uploader import YOWordPressUploader
    print(f"\n📤 WordPress'e yükleniyor → {site} / post {post_id}")

    uploader = YOWordPressUploader(site=site)

    result = uploader.upload_media(
        file_path=str(img_path),
        title=meta.get("title", img_path.stem),
        alt_text=meta.get("alt", ""),
        caption=meta.get("caption", ""),
        description=meta.get("description", ""),
    )

    if result.get("success"):
        media_id = result["media_id"]
        print(f"   ✅ Media ID: {media_id}")
        attach = uploader.attach_to_post(media_id=media_id, post_id=post_id)
        if attach.get("success"):
            print(f"   🔗 Post {post_id}'e eklendi")
        else:
            print(f"   ⚠️  Attach hatası: {attach.get('error')}")
    else:
        print(f"   ✗ Upload hatası: {result.get('error')}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query",                    help="Dosya adı (kısmi)")
    parser.add_argument("--post",     "-p",         type=int, default=None)
    parser.add_argument("--site",     "-s",         default="yoldaolmak")
    parser.add_argument("--location", "-l",         default="", help="Anahtar kelime / lokasyon")
    parser.add_argument("--dry-run",  "-n",         action="store_true", help="Dosyaya dokunmadan meta göster")
    args = parser.parse_args()

    out_path, meta = run(args.query, location=args.location, post_id=args.post,
                         site=args.site, dry_run=args.dry_run)

    if args.post and not args.dry_run:
        upload(out_path, meta, post_id=args.post, site=args.site)
