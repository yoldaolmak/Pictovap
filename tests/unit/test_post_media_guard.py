import json
from unittest.mock import MagicMock

from pictova.services.post_media_guard import (
    assess_post_media,
    load_post_media_manifest,
    media_items_from_content,
    save_post_media_manifest,
)
from pictova.services.wordpress import YOWordPressUploader


def test_media_items_from_content_keeps_nearest_heading():
    content = """
<h2>Karaburun Gezilecek Yerler</h2>
<!-- wp:gallery {"linkTo":"none"} -->
<figure class="wp-block-gallery has-nested-images">
<!-- wp:image {"id":11} -->
<figure class="wp-block-image"><img src="https://example.com/11.webp" alt="Koy" class="wp-image-11"/><figcaption>Kıyıda mola verdik.</figcaption></figure>
<!-- /wp:image -->
<!-- wp:image {"id":12} -->
<figure class="wp-block-image"><img src="https://example.com/12.webp" alt="Fener" class="wp-image-12"/></figure>
<!-- /wp:image -->
</figure>
<!-- /wp:gallery -->
"""

    items = media_items_from_content(content)

    assert [item["media_id"] for item in items] == [11, 12]
    assert all(item["heading"] == "Karaburun Gezilecek Yerler" for item in items)
    assert all(item["heading_level"] == 2 for item in items)
    assert items[0]["caption"] == "Kıyıda mola verdik."


def test_manifest_round_trip_merges_and_detects_drift(tmp_path, monkeypatch):
    monkeypatch.setenv("PICTOVA_POST_MANIFEST_DIR", str(tmp_path))
    first_content = '<img src="https://example.com/11.webp" class="wp-image-11"/>'
    second_content = first_content + '<img src="https://example.com/12.webp" class="wp-image-12"/>'

    save_post_media_manifest(
        site="yoldaolmak",
        post_id=267970,
        media_items=[{"media_id": 11, "url": "https://example.com/11.webp", "heading": "Koy"}],
        content_raw=first_content,
    )
    saved = save_post_media_manifest(
        site="yoldaolmak",
        post_id=267970,
        media_items=[{"media_id": 12, "url": "https://example.com/12.webp", "heading": "Fener"}],
        content_raw=second_content,
    )

    loaded = load_post_media_manifest("yoldaolmak", 267970)
    assert loaded is not None
    assert loaded["expected_media_ids"] == [11, 12]
    assert saved["manifest_path"].endswith("yoldaolmak-267970.json")
    assert json.loads((tmp_path / "yoldaolmak-267970.json").read_text())["version"] == 1

    healthy = assess_post_media(loaded, second_content)
    drift = assess_post_media(loaded, first_content)
    assert healthy["state"] == "healthy"
    assert drift["state"] == "drift"
    assert drift["missing_media_ids"] == [12]


def test_manifest_replaces_unanchored_auto_region_items(tmp_path, monkeypatch):
    monkeypatch.setenv("PICTOVA_POST_MANIFEST_DIR", str(tmp_path))
    both = '<i class="wp-image-1"></i><i class="wp-image-2"></i>'
    save_post_media_manifest(
        site="yoldaolmak",
        post_id=1,
        media_items=[{"media_id": 1, "url": "https://example.com/1.webp"}],
        content_raw=both,
    )
    saved = save_post_media_manifest(
        site="yoldaolmak",
        post_id=1,
        media_items=[{"media_id": 2, "url": "https://example.com/2.webp"}],
        content_raw=both,
    )

    assert saved["expected_media_ids"] == [2]


def test_guard_repairs_manifest_drift(tmp_path, monkeypatch):
    monkeypatch.setenv("PICTOVA_POST_MANIFEST_DIR", str(tmp_path))
    healthy_content = '<i class="wp-image-1"></i><i class="wp-image-2"></i>'
    drifted_content = '<i class="wp-image-1"></i>'
    save_post_media_manifest(
        site="yoldaolmak",
        post_id=99,
        media_items=[
            {"media_id": 1, "url": "https://example.com/1.webp", "heading": "Koy"},
            {"media_id": 2, "url": "https://example.com/2.webp", "heading": "Fener"},
        ],
        content_raw=healthy_content,
    )

    uploader = object.__new__(YOWordPressUploader)
    uploader.site = "yoldaolmak"
    uploader.fetch_post_context = MagicMock(side_effect=[
        {"content_raw": drifted_content},
        {"content_raw": healthy_content},
    ])
    uploader.append_media_to_post_content = MagicMock(return_value={"success": True})

    result = uploader.guard_post_media(99, repair=True)

    assert result["status"] == "success"
    assert result["state"] == "healthy"
    assert result["repaired"] is True
    uploader.append_media_to_post_content.assert_called_once()
    assert uploader.append_media_to_post_content.call_args.kwargs["allow_manifest_repair"] is True


def test_commit_aborts_when_post_changed_concurrently():
    uploader = object.__new__(YOWordPressUploader)
    uploader.site = "yoldaolmak"
    uploader.base_url = "https://example.com"
    uploader.session = MagicMock()
    uploader.fetch_post_context = MagicMock(return_value={
        "content_raw": "new editor content",
        "modified": "2026-06-28T16:10:00",
    })

    result = uploader._commit_post_content(
        post_id=99,
        original_content="old editor content",
        original_modified="2026-06-28T16:00:00",
        new_content="old editor content plus image",
        media_items=[{"media_id": 1, "url": "https://example.com/1.webp"}],
        inserted=1,
        removed_broken=0,
    )

    assert result["success"] is False
    assert result["code"] == "post_content_conflict"
    uploader.session.post.assert_not_called()
