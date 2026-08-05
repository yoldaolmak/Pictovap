"""Tests for local-only visual fingerprints and similarity scoring."""

from PIL import Image

from pictovap import compute_visual_fingerprint, visual_similarity
from pictovap.core.visual_similarity import collect_candidate_fingerprints


def test_near_duplicate_images_have_high_similarity(tmp_path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    other = tmp_path / "other.png"
    Image.new("RGB", (32, 32), (220, 220, 220)).save(first)
    Image.new("RGB", (32, 32), (218, 218, 218)).save(second)
    Image.new("RGB", (32, 32), (20, 40, 180)).save(other)

    first_fp = compute_visual_fingerprint(first)
    second_fp = compute_visual_fingerprint(second)
    other_fp = compute_visual_fingerprint(other)

    assert first_fp and second_fp and other_fp
    assert visual_similarity(first_fp, second_fp) > 0.95
    assert visual_similarity(first_fp, other_fp) < 0.9


def test_invalid_or_missing_local_files_are_ignored(tmp_path):
    candidates = [
        {"id": "missing", "local_path": str(tmp_path / "missing.png")},
        {"id": "invalid", "local_path": str(tmp_path / "invalid.png"), "visual_fingerprint": "bad"},
    ]
    (tmp_path / "invalid.png").write_text("not an image", encoding="utf-8")

    assert collect_candidate_fingerprints(candidates) == {}
