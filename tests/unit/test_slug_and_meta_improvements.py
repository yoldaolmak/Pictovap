"""Yeni iyileştirmeleri kapsayan unit testler:
- build_publish_slug: destinasyon prefix ekleme (gumusluk + bodrum-koy-kayalik)
- _enrich_from_cache: İngilizce scene → Türkçe çeviri
"""
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ── build_publish_slug: Destinasyon prefix ────────────────────────────────────

def test_slug_prepends_destination_when_stem_lacks_it(tmp_path):
    """bodrum-koy-kayalik.webp + post='gumusluk-gezilecek-yerler'
    → slug 'gumusluk-bodrum-koy-kayalik' (gumusluk öne eklenmiş)
    """
    from src.core.media_publish import build_publish_slug

    img = tmp_path / "bodrum-koy-kayalik_yo.webp"
    img.write_bytes(b"fake")

    post_context = {
        "title": "Gümüşlük Gezilecek Yerler",
        "slug": "gumusluk-gezilecek-yerler",
    }
    slug = build_publish_slug({}, post_context, str(img))

    assert "gumusluk" in slug, f"Beklenen 'gumusluk', alınan: {slug}"
    tokens = slug.split("-")
    assert tokens[0] == "gumusluk", f"Destinasyon başta olmalı; alınan: {slug}"
    assert len(tokens) <= 5, f"Max 5 token; alınan {len(tokens)}: {slug}"


def test_slug_does_not_double_destination_when_already_present(tmp_path):
    """gumusluk-koy.webp + post=gumusluk-... → gumusluk tekrarlanmamalı."""
    from src.core.media_publish import build_publish_slug

    img = tmp_path / "gumusluk-koy_yo.webp"
    img.write_bytes(b"fake")

    post_context = {"title": "Gümüşlük", "slug": "gumusluk-gezilecek-yerler"}
    slug = build_publish_slug({}, post_context, str(img))

    tokens = slug.split("-")
    assert tokens.count("gumusluk") == 1, (
        f"'gumusluk' yalnızca bir kez bulunmalı; alınan: {slug}"
    )


def test_slug_returns_valid_without_post_context(tmp_path):
    """Post context olmadan da slug üretilmeli; boş veya sadece '-' olmamalı."""
    from src.core.media_publish import build_publish_slug

    img = tmp_path / "xf23kabc_yo.webp"
    img.write_bytes(b"fake")

    slug = build_publish_slug({}, {}, str(img))
    assert slug and "-" in slug, f"Geçersiz slug: {slug!r}"

def test_slug_incorporates_heading_if_present(tmp_path):
    """Metadata içinde heading varsa slug'a dahil olmalı."""
    from src.core.media_publish import build_publish_slug

    img = tmp_path / "sahil-restoran_yo.webp"
    img.write_bytes(b"fake")

    metadata = {"heading": "10. Turgutreis"}
    post_context = {"slug": "bodrum-gezilecek-yerler"}
    
    slug = build_publish_slug(metadata, post_context, str(img))
    
    assert "turgutreis" in slug, f"Heading slug'a eklenmeli: {slug}"
    assert "bodrum" in slug, f"Post slug prefix'i (bodrum) korunmalı: {slug}"
    assert "10" not in slug, f"Numara prefix'leri atılmalı: {slug}"



# ── _enrich_from_cache: Scene İngilizce → Türkçe çeviri ──────────────────────

def test_enrich_from_cache_translates_english_scene_to_turkish():
    """DB'den 'coast' geldiğinde title/alt Türkçe 'kıyı' içermeli."""
    from src.pictova.engine.metadata import _enrich_from_cache

    cached = {
        "keywords": ["bodrum", "koy"],
        "scene": "coast",
        "activity": "travel",
        "summary": "",
    }
    post_ctx = {"title": "Gümüşlük Gezilecek Yerler"}
    result = _enrich_from_cache(cached, post_ctx)

    assert "coast" not in result["title"].lower(), (
        f"title Türkçe olmalı, 'coast' içermemeli: {result['title']}"
    )
    assert "coast" not in result["alt"].lower(), (
        f"alt Türkçe olmalı, 'coast' içermemeli: {result['alt']}"
    )
    assert "kıyı" in result["title"].lower() or "kıyı" in result["alt"].lower(), (
        f"'kıyı' title veya alt'ta bulunmalı: title={result['title']}, alt={result['alt']}"
    )


def test_enrich_from_cache_uses_turkish_summary_directly():
    """Summary Türkçe ise alt'a doğrudan koymalı."""
    from src.pictova.engine.metadata import _enrich_from_cache

    cached = {
        "keywords": ["bodrum"],
        "scene": "bay",
        "activity": "",
        "summary": "Teknelerin sığındığı sakin bir koy manzarası.",
    }
    post_ctx = {"title": "Gümüşlük"}
    result = _enrich_from_cache(cached, post_ctx)

    assert "Tekneler" in result["alt"], (
        f"Türkçe summary alt'a doğrudan gitmeli: {result['alt']}"
    )


def test_enrich_from_cache_skips_generic_scenes():
    """scene='general' generic → title'da yalnızca lokasyon olmalı."""
    from src.pictova.engine.metadata import _enrich_from_cache

    cached = {
        "keywords": ["bodrum"],
        "scene": "general",
        "activity": "",
        "summary": "",
    }
    post_ctx = {"title": "Bodrum"}
    result = _enrich_from_cache(cached, post_ctx)

    assert result["title"] == "Bodrum", (
        f"Generic scene'de title yalnızca lokasyon olmalı: {result['title']}"
    )
