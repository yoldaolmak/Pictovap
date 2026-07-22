import json

import pytest

from pictovap.feedback import summarize_plan


def test_summary_contains_only_anonymous_plan_statistics():
    plan = {
        "visual_brief": {
            "article_title": "Private title that must not leak",
            "source_path": "/redacted/private/article.md",
            "article_language": "en",
            "sections": [{"heading": "Private heading"}],
            "image_slots": [{"slot_id": "featured"}, {"slot_id": "body-1"}],
        },
        "candidates_evaluated": 4,
        "fit_scores": {"featured": [{"source_url": "https://private.example"}]},
        "provenance_packs": [{"source_url": "https://private.example"}],
        "cms_placement": {"placements": [{"output_path": "private.webp"}]},
        "profile": {"id": "private-profile"},
        "runtime": {"provider": {"mode": "plugin", "name": "private-provider"}},
    }

    serialized = json.dumps(summarize_plan(plan))

    assert "Private title" not in serialized
    assert "/redacted/private" not in serialized
    assert "private.example" not in serialized
    assert "private-provider" not in serialized
    assert summarize_plan(plan)["plan"] == {
        "article_language": "en",
        "sections": 1,
        "image_slots": 2,
        "candidates_evaluated": 4,
        "scored_candidates": 1,
        "selected_images": 1,
        "placements": 1,
    }


def test_summary_handles_partial_plan():
    summary = summarize_plan({"visual_brief": {"sections": []}})

    assert summary["plan"]["sections"] == 0
    assert summary["plan"]["selected_images"] == 0
    assert summary["runtime"]["provider_mode"] is None


def test_summary_requires_object():
    with pytest.raises(ValueError, match="must contain an object"):
        summarize_plan([])
