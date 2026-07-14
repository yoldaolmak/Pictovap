"""
Unit tests for the core Pictovap primitives.
Ensures that the models can be instantiated and serialized correctly.
"""

from datetime import datetime, timezone

from pictovap.core.primitives import (
    VisualBrief,
    FitScore,
    ProvenancePack,
    CMSPlacement,
    PlacementInstruction
)
from pictovap.core.profile import PublisherProfile


def test_visual_brief_serialization():
    brief = VisualBrief(
        article_title="Test Title",
        topic="Testing",
        sections=[{"heading": "Intro"}],
        image_slots=[{"slot_id": "featured", "purpose": "featured_image"}]
    )
    
    data = brief.to_dict()
    assert data["article_title"] == "Test Title"
    assert data["topic"] == "Testing"
    assert len(data["sections"]) == 1
    assert data["sections"][0]["heading"] == "Intro"
    assert len(data["image_slots"]) == 1
    assert data["image_slots"][0]["slot_id"] == "featured"


def test_fit_score_rejection():
    score = FitScore(
        candidate_id="img-1",
        final_score=1.5,
        decision="rejected",
        human_reason="Low resolution"
    )
    
    data = score.to_dict()
    assert data["candidate_id"] == "img-1"
    assert data["final_score"] == 1.5
    assert data["decision"] == "rejected"
    assert data["human_reason"] == "Low resolution"


def test_provenance_pack():
    pack = ProvenancePack(
        image_id="img-2",
        source_url="http://example.com/img.jpg",
        local_source_path="/tmp/img.jpg",
        provider="test-provider",
        original_filename="img.jpg",
        generated_filename="final.webp",
        content_hash="hash123",
        slot_id="hero",
        placement_target="hero_header",
        generated_alt_text="Alt",
        generated_caption="Cap"
    )
    
    data = pack.to_dict()
    assert data["image_id"] == "img-2"
    assert data["provider"] == "test-provider"
    assert data["slot_id"] == "hero"
    # Should automatically set timestamp
    assert "timestamp" in data
    timestamp = datetime.fromisoformat(data["timestamp"])
    assert timestamp.utcoffset() == timezone.utc.utcoffset(timestamp)


def test_cms_placement():
    placement = CMSPlacement(
        article_id="post-99",
        target_platform="wordpress",
        adapter_target="wp_gutenberg",
        placements=[
            PlacementInstruction(
                slot_id="hero",
                output_path="final.webp",
                target_section="hero",
                alt_text="Alt"
            )
        ]
    )
    
    data = placement.to_dict()
    assert data["article_id"] == "post-99"
    assert data["target_platform"] == "wordpress"
    assert data["adapter_target"] == "wp_gutenberg"
    assert len(data["placements"]) == 1
    assert data["placements"][0]["slot_id"] == "hero"
    assert data["placements"][0]["output_path"] == "final.webp"

    restored = CMSPlacement.from_dict(data)
    assert restored == placement


def test_cms_placement_from_dict_rejects_incomplete_payload():
    try:
        CMSPlacement.from_dict({"article_id": "post-99"})
    except ValueError as error:
        assert "placements" in str(error)
    else:
        raise AssertionError("Expected an incomplete placement to fail")

def test_publisher_profile():
    profile = PublisherProfile.get_default_profile()
    assert profile.profile_id == "demo"
    assert profile.brand_name == "Demo Publisher"
    assert "local" in profile.image_sources
    assert isinstance(profile.forbidden_patterns, list)
