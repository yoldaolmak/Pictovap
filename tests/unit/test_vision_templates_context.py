"""Prompt context stays bounded so article metadata cannot inflate model cost."""

from pictovap.vision_templates import TRAVEL_BLOG


def test_travel_prompt_bounds_location_and_labels():
    prompt = TRAVEL_BLOG.build_prompt(
        "L" * 1000,
        {"title": "T" * 1000, "apple_labels": ["label-" + ("x" * 200)] * 20},
    )

    assert len(prompt) < 2500
    assert "L" * 120 in prompt
    assert "L" * 121 not in prompt
