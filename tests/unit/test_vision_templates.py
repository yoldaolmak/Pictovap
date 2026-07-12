"""Unit tests for the VisionTemplate system."""
from __future__ import annotations

import pytest

from pictovap.vision_templates import (
    VisionTemplate,
    TRAVEL_BLOG,
    TECHNICAL,
    MINIMAL,
    ECOMMERCE,
    get_template,
    register_template,
)


def test_travel_blog_prompt_contains_json_schema():
    prompt = TRAVEL_BLOG.build_prompt("Akyaka", {"title": "Akyaka Rehberi"})
    assert "alt" in prompt
    assert "caption" in prompt
    assert "story_score" in prompt


def test_technical_prompt_outputs_english():
    prompt = TECHNICAL.build_prompt("Istanbul", {})
    assert "English" in prompt or "english" in prompt.lower()
    assert "alt" in prompt


def test_minimal_prompt_is_shorter_than_travel_blog():
    ctx = {"title": "Test"}
    assert len(MINIMAL.build_prompt("loc", ctx)) < len(TRAVEL_BLOG.build_prompt("loc", ctx))


def test_ecommerce_prompt_mentions_product():
    prompt = ECOMMERCE.build_prompt("Widget X", {"title": "Widget X"})
    assert "product" in prompt.lower() or "ecommerce" in prompt.lower()


def test_get_template_returns_correct_instance():
    t = get_template("technical")
    assert t.name == "technical"
    assert t is TECHNICAL


def test_get_template_raises_for_unknown_name():
    with pytest.raises(KeyError, match="unknown_xyz"):
        get_template("unknown_xyz")


def test_register_and_retrieve_custom_template():
    custom = VisionTemplate(
        name="test_custom_template",
        description="Test template",
        prompt_fn=lambda loc, ctx: f"Analyze {loc}. Return JSON.",
    )
    register_template(custom)
    retrieved = get_template("test_custom_template")
    assert retrieved is custom
    assert retrieved.build_prompt("Paris", {}) == "Analyze Paris. Return JSON."


def test_custom_template_via_string_in_chain(monkeypatch):
    """analyze_image_vision_chain accepts a template name string."""
    from pictovap.engine import vision_chain as vc

    captured = {}

    def mock_analyze(image_path, location_hint, post_context, template=None):
        captured["template"] = template
        return {
            "alt": "test", "title": "t", "caption": "c",
            "description": "d", "summary": "s", "keywords": [],
            "people": [], "scene": "x", "activity": "y", "story_score": 0.5,
        }

    monkeypatch.setattr(vc, "_analyze_lm_studio", mock_analyze)

    result = vc.analyze_image_vision_chain(
        "fake_path.jpg",
        location_hint="loc",
        post_context={},
        template="technical",
    )
    assert result["alt"] == "test"
    assert captured["template"].name == "technical"


def test_builtin_template_via_object_in_chain(monkeypatch):
    """analyze_image_vision_chain accepts a VisionTemplate object."""
    from pictovap.engine import vision_chain as vc

    captured = {}

    def mock_analyze(image_path, location_hint, post_context, template=None):
        captured["template"] = template
        return {
            "alt": "a", "title": "t", "caption": "c", "description": "d",
            "summary": "s", "keywords": [], "people": [],
            "scene": "x", "activity": "y", "story_score": 0.7,
        }

    monkeypatch.setattr(vc, "_analyze_lm_studio", mock_analyze)

    vc.analyze_image_vision_chain(
        "fake.jpg",
        location_hint="Istanbul",
        post_context={},
        template=ECOMMERCE,
    )
    assert captured["template"] is ECOMMERCE
