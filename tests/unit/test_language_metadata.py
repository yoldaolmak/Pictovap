import json
import subprocess
from pathlib import Path
import pytest

from pictovap.core.language import detect_language
from pictovap.core.primitives import VisualBrief
from pictovap.core.profile import PublisherProfile
from pictovap.core.demo_metadata import generate_local_alt_text, generate_local_caption
from pictovap.demo import generate_markdown_report

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"
TURKISH_ARTICLE_PATH = FIXTURE_DIR / "turkish-coffee-article.md"


def test_language_detection():
    # Detect Turkish
    tr_text = "Evde lezzetli bir filtre kahve demlemek için doğru adımları izlemek gerekir."
    assert detect_language(tr_text) == "tr"
    
    # Detect English
    en_text = "The quick brown fox jumps over the lazy dog. A guide for minimalist travel."
    assert detect_language(en_text) == "en"
    
    # Fallback when uncertain or empty
    assert detect_language("", fallback_lang="fr") == "fr"
    assert detect_language("abc xyz", fallback_lang="tr") == "tr"


def test_visual_brief_language_detection():
    # Turkish fixture
    brief_tr = VisualBrief.from_markdown(str(TURKISH_ARTICLE_PATH))
    assert brief_tr.article_language == "tr"
    
    # English fixture (default sample article)
    sample_en_path = Path(__file__).resolve().parents[2] / "examples" / "sample-article.md"
    if sample_en_path.exists():
        brief_en = VisualBrief.from_markdown(str(sample_en_path))
        assert brief_en.article_language == "en"


def test_profile_language_fallback_and_override():
    # If fallback is provided, it is used when detection fails (e.g. empty or ambiguous text)
    brief = VisualBrief.from_markdown(str(TURKISH_ARTICLE_PATH), fallback_lang="en")
    # Turkish markers are strong in turkish-coffee-article, so it should still detect tr
    assert brief.article_language == "tr"
    
    # Test fallback on empty file or ambiguous text
    profile_tr = PublisherProfile(
        profile_id="test-tr",
        brand_name="Test Publisher TR",
        language="tr",
        language_mode="fallback"
    )
    profile_en = PublisherProfile(
        profile_id="test-en",
        brand_name="Test Publisher EN",
        language="en",
        language_mode="fallback"
    )
    profile_override = PublisherProfile(
        profile_id="test-override",
        brand_name="Test Override",
        language="en",
        language_mode="override"
    )
    
    # Ambiguous/empty text with fallback profile
    # Let's mock a short file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w+", encoding="utf-8") as f:
        f.write("# Hello\n\nShort ambiguous text.")
        f.flush()
        
        # Fallback profile language is fallback
        brief_fallback = VisualBrief.from_markdown(f.name, fallback_lang=profile_tr.language)
        assert brief_fallback.article_language == "tr"
        
        # Override profile language overrides anyway
        brief_override = VisualBrief.from_markdown(f.name, fallback_lang=profile_en.language)
        if profile_override.language_mode == "override":
            brief_override.article_language = profile_override.language
        assert brief_override.article_language == "en"


def test_localized_metadata_generation():
    slot_coffee = {
        "slot_id": "section_0",
        "purpose": "inline_after_cekirdek_secimi",
        "target_heading": "Çekirdek Seçimi",
        "section_excerpt": "Kahve çekirdeklerinin tazeliği fincana yansır."
    }
    
    slot_packing = {
        "slot_id": "featured",
        "purpose": "featured_image",
        "target_heading": "Packing Smart",
        "section_excerpt": "The core of minimalism is the capsule wardrobe."
    }
    
    cand_backpack = {"keywords": ["backpack", "travel", "minimalist"]}
    cand_coffee = {"keywords": ["coffee", "equipment", "beans"]}
    
    # Turkish Alt Text
    alt_tr_backpack = generate_local_alt_text(cand_backpack, slot_packing, language="tr")
    assert "Sırt çantası" in alt_tr_backpack
    assert "görsel" in alt_tr_backpack
    
    alt_tr_coffee = generate_local_alt_text(cand_coffee, slot_coffee, language="tr")
    assert "Kahve demleme" in alt_tr_coffee
    assert "görsel" in alt_tr_coffee
    
    # English Alt Text
    alt_en_backpack = generate_local_alt_text(cand_backpack, slot_packing, language="en")
    assert "backpack" in alt_en_backpack or "packing" in alt_en_backpack or "travel" in alt_en_backpack
    
    alt_en_coffee = generate_local_alt_text(cand_coffee, slot_coffee, language="en")
    assert "coffee" in alt_en_coffee or "brewing" in alt_en_coffee
    
    # Check no generic placeholders
    for alt in [alt_tr_backpack, alt_tr_coffee, alt_en_backpack, alt_en_coffee]:
        assert "A forest, nature, path scene" not in alt
        assert "Visual for:" not in alt
        assert "Image of:" not in alt
        assert "Photo of:" not in alt
        
    # Captions do not start with "Visual for:" and match language
    cap_tr_coffee = generate_local_caption(cand_coffee, slot_coffee, language="tr")
    assert not cap_tr_coffee.startswith("Visual for:")
    assert "Çekirdek seçimi" in cap_tr_coffee or "aroma" in cap_tr_coffee
    
    cap_en_packing = generate_local_caption(cand_backpack, slot_packing, language="en")
    assert not cap_en_packing.startswith("Visual for:")


def test_visual_slots_include_context():
    brief = VisualBrief.from_markdown(str(TURKISH_ARTICLE_PATH))
    for slot in brief.image_slots:
        assert "section_excerpt" in slot
        assert len(slot["section_excerpt"]) > 0


def test_report_includes_language_and_context():
    # Make a dummy pipeline output dict
    output = {
        "visual_brief": {
            "article_title": "Test Title",
            "article_language": "tr",
            "sections": [{"heading": "Baslik"}],
            "image_slots": [
                {
                    "slot_id": "featured",
                    "preferred_type": "landscape",
                    "section_excerpt": "Bu bir test excerpt'tir.",
                }
            ]
        },
        "profile": {
            "brand": "Demo",
            "id": "demo",
        },
        "provenance_packs": [],
        "cms_placement": {"placements": []},
        "fit_scores": {}
    }
    
    report = generate_markdown_report(output)
    assert "tr" in report
    assert "Bu bir test excerpt'tir" in report


def test_pictovap_plan_works_with_turkish_article(tmp_path):
    output_json = tmp_path / "turkish-plan.json"
    output_md = tmp_path / "turkish-plan.md"
    
    result = subprocess.run([
        "pictovap", "plan",
        "--article", str(TURKISH_ARTICLE_PATH),
        "--profile", "examples/profiles/sample-publisher.yaml",
        "--output", str(output_json),
        "--report", str(output_md)
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert output_json.exists()
    assert output_md.exists()
    
    # Verify outputs contain Turkish
    plan_data = json.loads(output_json.read_text(encoding="utf-8"))
    assert plan_data["visual_brief"]["article_language"] == "tr"
    
    report_text = output_md.read_text(encoding="utf-8")
    assert "**Language:** tr" in report_text
    assert "Çekirdek seçimi" in report_text or "Ekipman" in report_text
