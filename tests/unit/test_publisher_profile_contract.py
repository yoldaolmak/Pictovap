from __future__ import annotations

from pathlib import Path

import pytest

from pictovap.core.profile import PROFILE_SCHEMA_VERSION, PublisherProfile, PublisherProfileError


def test_all_shipped_profiles_satisfy_the_v1_contract():
    root = Path(__file__).resolve().parents[2]
    for profile_path in (root / "examples" / "profiles").glob("*.yaml"):
        profile = PublisherProfile.from_yaml(profile_path)
        assert profile.schema_version == PROFILE_SCHEMA_VERSION


def test_profile_rejects_unknown_fields():
    with pytest.raises(PublisherProfileError, match="Unknown"):
        PublisherProfile.from_mapping({
            "schema_version": 1,
            "profile_id": "example",
            "brand_name": "Example",
            "made_up_setting": True,
        })


@pytest.mark.parametrize("data, message", [
    ({"profile_id": "example", "brand_name": "Example"}, "schema_version"),
    ({"schema_version": 2, "profile_id": "example", "brand_name": "Example"}, "Unsupported"),
    ({"schema_version": 1, "profile_id": "Example", "brand_name": "Example"}, "profile_id"),
    ({"schema_version": 1, "profile_id": "example", "brand_name": "Example", "image_sources": []}, "image_sources"),
])
def test_profile_rejects_invalid_contract_data(data, message):
    with pytest.raises(PublisherProfileError, match=message):
        PublisherProfile.from_mapping(data)


def test_profile_loader_supports_real_yaml_strings_and_comments(tmp_path):
    path = tmp_path / "profile.yaml"
    path.write_text(
        """# A user-editable profile\nschema_version: 1\nprofile_id: editor-blog\nbrand_name: Editor Blog\nimage_sources: [local, openverse]\ncaption_rules:\n  include_attribution: true\n""",
        encoding="utf-8",
    )

    profile = PublisherProfile.from_yaml(path)

    assert profile.image_sources == ["local", "openverse"]
    assert profile.caption_rules == {"include_attribution": True}
