from __future__ import annotations

import io
import json
import os
import urllib.error
from copy import deepcopy

import pytest
from PIL import Image

from pictovap import (
    build_decision_pack,
    validate_decision_pack,
    validate_visual_plan,
)
from pictovap.app.runtime import PipelineRunner, _validate_safe_output_path
from pictovap.core.primitives import CMSPlacement, PlacementInstruction, VisualBrief
from pictovap.engine.scoring import score_candidate
from pictovap.engine.vision_chain import _analyze_gemini_flash
from pictovap.providers.deposit import DepositPhotosSource
from pictovap.providers.unsplash import UnsplashSource
from pictovap.publishers.ghost import GhostPublisher
from pictovap.publishers.strapi import StrapiPublisher
from pictovap.services.wordpress import WordPressUploader
from pictovap.testing import (
    sample_decision_pack,
    sample_visual_plan,
    validate_candidates,
)
from pictovap.utils import config


# 1. DepositPhotos adapter tests
def test_depositphotos_search_candidates_passes_validate_candidates(monkeypatch):
    monkeypatch.setenv("DEPOSIT_API_KEY", "dummy_key")
    mock_resp = {
        "type": "success",
        "result": [
            {
                "id": "12345",
                "title": "Beautiful Mountain Sunrise",
                "width": 4000,
                "height": 2600,
                "downloads": 50,
                "url_big": "https://example.com/big.jpg",
            }
        ],
    }
    monkeypatch.setattr("pictovap.providers.deposit._post", lambda payload: mock_resp)

    candidates = DepositPhotosSource().search_candidates("mountain", count=1)
    assert len(candidates) == 1
    validate_candidates(candidates)
    assert candidates[0]["width"] == 4000
    assert candidates[0]["height"] == 2600
    assert candidates[0]["provider"] == "depositphotos"


def test_depositphotos_degrades_to_empty_list_on_urlerror(monkeypatch):
    monkeypatch.setenv("DEPOSIT_API_KEY", "dummy_key")

    def _mock_urlopen(req, timeout=30):
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr("urllib.request.urlopen", _mock_urlopen)
    candidates = DepositPhotosSource().search_candidates("mountain", count=1)
    assert candidates == []


# 2. Scoring engine normalization tests
def test_score_candidate_normalizes_license_and_provider():
    brief = VisualBrief(
        article_id="test-1",
        article_title="Exploring Nature",
        topic="Nature exploration",
        image_slots=[{"slot_id": "featured", "purpose": "featured_image"}],
    )
    slot = {
        "slot_id": "featured",
        "purpose": "featured_image",
        "target_heading": "Exploring Nature",
    }

    # Lowercase cc0 license, openverse provider
    cand_openverse = {
        "id": "cand-ov",
        "license": "cc0",
        "provider": "OpenVerse",
        "width": 1600,
        "height": 1000,
        "keywords": ["nature", "mountain"],
    }
    score_ov = score_candidate(cand_openverse, slot, brief)
    assert score_ov.license_confidence == 2.0
    assert score_ov.source_trust == 1.5

    # Pexels provider, pexels license
    cand_pexels = {
        "id": "cand-px",
        "license": "PEXELS",
        "provider": "Pexels",
        "width": 1600,
        "height": 1000,
        "keywords": ["nature"],
    }
    score_px = score_candidate(cand_pexels, slot, brief)
    assert score_px.license_confidence == 1.5
    assert score_px.source_trust == 1.5

    # Depositphotos provider, editorial license
    cand_deposit = {
        "id": "cand-dp",
        "license": "editorial",
        "provider": "DepositPhotos",
        "width": 1600,
        "height": 1000,
        "keywords": ["nature"],
    }
    score_dp = score_candidate(cand_deposit, slot, brief)
    assert score_dp.license_confidence == 0.5
    assert score_dp.source_trust == 1.5


# 3. Vision chain API key protection tests
def test_analyze_gemini_flash_does_not_leak_api_key_on_error(monkeypatch, tmp_path):
    secret_key = "AIzaSySUPER_SECRET_KEY_12345"
    monkeypatch.setenv("GEMINI_API_KEY", secret_key)

    img_path = tmp_path / "test.jpg"
    Image.new("RGB", (100, 100), color="red").save(img_path)

    # Test HTTPError
    def mock_urlopen_http(*args, **kwargs):
        endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        raise urllib.error.HTTPError(
            url=f"{endpoint}?key={secret_key}",
            code=400,
            msg="Bad Request",
            hdrs={},  # type: ignore[arg-type]
            fp=io.BytesIO(b"error details"),
        )

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_http)

    with pytest.raises(RuntimeError) as exc_info:
        _analyze_gemini_flash(str(img_path), "test location", {"title": "Test"})

    assert secret_key not in str(exc_info.value)
    assert secret_key not in repr(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__suppress_context__ is True

    # Test URLError
    def mock_urlopen_url(*args, **kwargs):
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_url)

    with pytest.raises(RuntimeError) as exc_info:
        _analyze_gemini_flash(str(img_path), "test location", {"title": "Test"})

    assert secret_key not in str(exc_info.value)
    assert secret_key not in repr(exc_info.value)
    assert "Connection refused" in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__suppress_context__ is True


# 4. Config env quote stripping tests
def test_load_project_env_strips_single_and_double_quotes(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        'TEST_DOUBLE="hello world"\n'
        "TEST_SINGLE='single quote value'\n"
        "TEST_BARE=bare value\n"
        'TEST_EMPTY=""\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "_ENV_LOADED", False)
    monkeypatch.setattr(config, "get_workspace_root", lambda: tmp_path)

    config.load_project_env()

    assert os.environ.get("TEST_DOUBLE") == "hello world"
    assert os.environ.get("TEST_SINGLE") == "single quote value"
    assert os.environ.get("TEST_BARE") == "bare value"
    assert os.environ.get("TEST_EMPTY") == ""


# 5. Runtime path validation & pre-publish visual plan validation tests
def test_pipeline_runner_publish_rejects_invalid_plan(tmp_path):
    invalid_plan = tmp_path / "invalid_plan.json"
    invalid_plan.write_text(
        json.dumps({
            "visual_brief": {"article_title": ""},
            "cms_placement": {"article_id": "test", "placements": []},
        }),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Visual plan failed validation before publish"):
        PipelineRunner().publish(plan=str(invalid_plan), cms="wordpress", dry_run=True)


def test_pipeline_runner_publish_rejects_unsafe_output_paths(tmp_path):
    # Dotfile test (.env)
    plan_dotfile = sample_visual_plan("test-dot")
    plan_dotfile["cms_placement"]["placements"][0]["output_path"] = ".env"
    plan_path_1 = tmp_path / "plan_dot.json"
    plan_path_1.write_text(json.dumps(plan_dotfile), encoding="utf-8")

    with pytest.raises(ValueError, match="Unsafe placement output_path rejected"):
        PipelineRunner().publish(plan=str(plan_path_1), cms="wordpress", dry_run=True)

    # Path traversal test (../secret.webp)
    plan_traversal = sample_visual_plan("test-trav")
    plan_traversal["cms_placement"]["placements"][0]["output_path"] = "../secret.webp"
    plan_path_2 = tmp_path / "plan_trav.json"
    plan_path_2.write_text(json.dumps(plan_traversal), encoding="utf-8")

    with pytest.raises(ValueError, match="Unsafe placement output_path rejected"):
        PipelineRunner().publish(plan=str(plan_path_2), cms="wordpress", dry_run=True)


# 6. CMS Uploader path traversal defense & batch reuse tests
def test_cms_uploaders_reject_unsafe_paths(monkeypatch):
    monkeypatch.setenv("WP_URL", "https://wp.example.com")
    monkeypatch.setenv("WP_USER", "admin")
    monkeypatch.setenv("WP_APP_PASSWORD", "secret")
    monkeypatch.setenv("GHOST_URL", "https://ghost.example.com")
    monkeypatch.setenv("GHOST_ADMIN_API_KEY", "id:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
    monkeypatch.setenv("STRAPI_URL", "https://strapi.example.com")
    monkeypatch.setenv("STRAPI_API_TOKEN", "strapi_secret")

    wp = WordPressUploader()
    ghost = GhostPublisher()
    strapi = StrapiPublisher()

    for uploader in (wp, ghost, strapi):
        # Traversal path
        res_trav = uploader.upload_media(file_path="../secret.png", title="T", alt_text="A")
        assert res_trav["success"] is False
        assert "Unsafe file path rejected" in res_trav["error"]

        # Dotfile path
        res_dot = uploader.upload_media(file_path=".env", title="T", alt_text="A")
        assert res_dot["success"] is False
        assert "Unsafe file path rejected" in res_dot["error"]

        # Empty path
        res_empty = uploader.upload_media(file_path="", title="T", alt_text="A")
        assert res_empty["success"] is False
        assert "Unsafe file path rejected" in res_empty["error"]


def test_wordpress_place_reuses_uploader_instance(monkeypatch):
    monkeypatch.setenv("WP_URL", "https://wp.example.com")
    monkeypatch.setenv("WP_USER", "admin")
    monkeypatch.setenv("WP_APP_PASSWORD", "secret")

    uploader = WordPressUploader()
    captured_uploader = None

    def mock_upload_images_batch(image_files, metadata_dict, post_id, site="demo", uploader=None):
        nonlocal captured_uploader
        captured_uploader = uploader
        return {"uploaded": [], "failed": []}

    monkeypatch.setattr("pictovap.services.wordpress.upload_images_batch", mock_upload_images_batch)

    placement = CMSPlacement(
        article_id="123",
        placements=[PlacementInstruction(
            slot_id="featured",
            output_path="/tmp/image.webp",
            image_role="featured",
            alt_text="Alt",
            caption="Caption",
        )],
    )

    uploader.place(placement)
    assert captured_uploader is uploader


# 7. Decision pack & contracts tests
def test_sample_fixtures_pass_validation():
    plan = sample_visual_plan("test-fixture")
    v_plan = validate_visual_plan(plan)
    assert v_plan["status"] == "passed"

    pack = sample_decision_pack("test-fixture")
    v_pack = validate_decision_pack(pack)
    assert v_pack["status"] == "passed"


def test_decision_pack_input_immutability():
    pack = sample_decision_pack("test-fixture")
    pack_clone = deepcopy(pack)

    validate_decision_pack(pack)
    assert pack == pack_clone


def test_build_decision_pack_optional_metadata():
    plan = sample_visual_plan("test-meta")

    # Default has no pack_id or engine_version
    pack_default = build_decision_pack(plan)
    assert "pack_id" not in pack_default
    assert "engine_version" not in pack_default

    # With pack_id and engine_version
    pack_custom = build_decision_pack(
        plan,
        pack_id="pack-001",
        engine_version="0.13.0",
    )
    assert pack_custom["pack_id"] == "pack-001"
    assert pack_custom["engine_version"] == "0.13.0"
    v_custom = validate_decision_pack(pack_custom)
    assert v_custom["status"] == "passed"

    # Invalid pack_id
    with pytest.raises(ValueError, match="pack_id must be a non-empty string"):
        build_decision_pack(plan, pack_id="")

    # Invalid engine_version
    with pytest.raises(ValueError, match="engine_version must be a non-empty string"):
        build_decision_pack(plan, engine_version="  ")

    # validate_decision_pack catches invalid pack_id in dict
    pack_bad = deepcopy(pack_custom)
    pack_bad["pack_id"] = ""
    v_bad = validate_decision_pack(pack_bad)
    assert v_bad["status"] == "failed"
    assert any(err["code"] == "decision_pack_id" for err in v_bad["errors"])

    # validate_decision_pack catches invalid engine_version in dict
    pack_bad_v = deepcopy(pack_custom)
    pack_bad_v["engine_version"] = 123  # not string
    v_bad_v = validate_decision_pack(pack_bad_v)
    assert v_bad_v["status"] == "failed"
    assert any(err["code"] == "decision_pack_engine_version" for err in v_bad_v["errors"])


# 8. Remediated security regression tests
def test_validate_safe_output_path_enforces_relative_images(tmp_path):
    with pytest.raises(ValueError, match="Unsafe placement output_path rejected"):
        _validate_safe_output_path("/etc/passwd")

    with pytest.raises(ValueError, match="Unsafe placement output_path rejected"):
        _validate_safe_output_path("script.py")

    with pytest.raises(ValueError, match="Unsafe placement output_path rejected"):
        _validate_safe_output_path("images/.hidden.webp")

    # Symlink output path test
    target_img = tmp_path / "real.webp"
    target_img.write_bytes(b"data")
    sym = tmp_path / "sym.webp"
    sym.symlink_to(target_img)
    with pytest.raises(ValueError, match="Unsafe placement output_path rejected"):
        _validate_safe_output_path(str(sym))

    # Valid relative images pass
    _validate_safe_output_path("images/hero.webp")
    _validate_safe_output_path("images/section.png")
    _validate_safe_output_path("images/photo.jpg")


def test_upload_media_rejects_non_images_symlinks_and_system_files(tmp_path, monkeypatch):
    monkeypatch.setenv("WP_URL", "https://wp.example.com")
    monkeypatch.setenv("WP_USER", "admin")
    monkeypatch.setenv("WP_APP_PASSWORD", "secret")
    monkeypatch.setenv("GHOST_URL", "https://ghost.example.com")
    monkeypatch.setenv("GHOST_ADMIN_API_KEY", "id:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
    monkeypatch.setenv("STRAPI_URL", "https://strapi.example.com")
    monkeypatch.setenv("STRAPI_API_TOKEN", "strapi_secret")

    wp = WordPressUploader()
    ghost = GhostPublisher()
    strapi = StrapiPublisher()

    text_file = tmp_path / "secret.txt"
    text_file.write_text("secrets", encoding="utf-8")

    real_img = tmp_path / "real.webp"
    real_img.write_bytes(b"RIFF....WEBP")

    symlink_img = tmp_path / "symlink.webp"
    symlink_img.symlink_to(real_img)

    for uploader in (wp, ghost, strapi):
        # Non-image extension rejected
        res_txt = uploader.upload_media(file_path=str(text_file), title="T", alt_text="A")
        assert res_txt["success"] is False
        assert "Unsafe file path rejected" in res_txt["error"]

        # Symlink rejected
        res_sym = uploader.upload_media(file_path=str(symlink_img), title="T", alt_text="A")
        assert res_sym["success"] is False
        assert "Unsafe file path rejected" in res_sym["error"]

        # Arbitrary system file rejected
        res_sys = uploader.upload_media(file_path="/etc/passwd", title="T", alt_text="A")
        assert res_sys["success"] is False
        assert "Unsafe file path rejected" in res_sys["error"]


def test_cms_base_url_scheme_validation(monkeypatch):
    # Ghost
    with pytest.raises(ValueError, match="valid http or https URL"):
        GhostPublisher(ghost_url="ftp://example.ghost.io", admin_api_key="id:key")
    with pytest.raises(ValueError, match="valid http or https URL"):
        GhostPublisher(ghost_url="file:///etc/passwd", admin_api_key="id:key")

    # Strapi
    with pytest.raises(ValueError, match="valid http or https URL"):
        StrapiPublisher(strapi_url="javascript:alert(1)", api_token="secret")
    with pytest.raises(ValueError, match="valid http or https URL"):
        StrapiPublisher(strapi_url="cms.example.com", api_token="secret")

    # WordPress
    monkeypatch.setenv("WP_URL", "ftp://wp.example.com")
    monkeypatch.setenv("WP_USER", "admin")
    monkeypatch.setenv("WP_APP_PASSWORD", "secret")
    with pytest.raises(ValueError, match="valid http or https URL"):
        WordPressUploader()


def test_unsplash_search_passes_api_key_in_auth_header_not_params(monkeypatch):
    monkeypatch.setenv("UNSPLASH_ACCESS_KEY", "secret-unsplash-key")
    source = UnsplashSource()

    captured_kwargs = {}

    def mock_get(url, **kwargs):
        captured_kwargs.update(kwargs)
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        return mock_response

    import unittest.mock
    from unittest.mock import MagicMock
    monkeypatch.setattr("requests.get", mock_get)

    results = source.search("travel", count=3)
    assert results == []
    assert "client_id" not in captured_kwargs.get("params", {})
    assert captured_kwargs.get("headers", {}).get("Authorization") == "Client-ID secret-unsplash-key"


def test_gemini_vision_passes_api_key_in_header_not_query(monkeypatch, tmp_path):
    secret_key = "AIzaSyTEST_HEADER_KEY_67890"
    monkeypatch.setenv("GEMINI_API_KEY", secret_key)

    img_path = tmp_path / "test.jpg"
    Image.new("RGB", (100, 100), color="blue").save(img_path)

    captured_req = []

    def mock_urlopen(req, *args, **kwargs):
        captured_req.append(req)
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{"text": '{"description": "A blue test image", "suggested_alt": "Blue test"}'}]
                }
            }]
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    from unittest.mock import MagicMock
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)

    result = _analyze_gemini_flash(str(img_path), "test hint", {"title": "Test"})
    assert "description" in result

    assert len(captured_req) == 1
    req = captured_req[0]
    assert "?key=" not in req.full_url
    assert secret_key not in req.full_url
    assert req.headers.get("X-goog-api-key") == secret_key


def test_wordpress_insert_media_blocks_escapes_image_url(monkeypatch, tmp_path):
    monkeypatch.setenv("WP_URL", "https://wp.example.com")
    monkeypatch.setenv("WP_USER", "admin")
    monkeypatch.setenv("WP_APP_PASSWORD", "secret")
    monkeypatch.setenv("PICTOVAP_POST_MANIFEST_DIR", str(tmp_path / "manifests"))

    uploader = WordPressUploader()

    current_post_content = "<!-- wp:heading -->\n<h2>Travel Tips</h2>\n<!-- /wp:heading -->\n<p>Body</p>"

    def mock_fetch(post_id):
        return {"content_raw": current_post_content, "id": post_id}

    monkeypatch.setattr(uploader, "fetch_post_context", mock_fetch)

    captured_updates = []

    def mock_post(url, **kwargs):
        nonlocal current_post_content
        payload = kwargs.get("json", {})
        if "content" in payload:
            current_post_content = payload["content"]
        captured_updates.append(payload)
        resp = MagicMock()
        resp.raise_for_status = lambda: None
        resp.json.return_value = {"id": 42}
        return resp

    from unittest.mock import MagicMock
    monkeypatch.setattr(uploader.session, "post", mock_post)

    media_items = [
        {
            "media_id": 101,
            "url": 'https://example.com/pic.jpg?x=1&y=2" onerror="alert(1)',
            "alt": 'Alt " quote',
            "caption": 'Caption <script>',
            "heading": "Travel Tips",
        }
    ]

    result = uploader.append_media_to_post_content(post_id=42, media_items=media_items)
    assert result.get("success") is True

    assert len(captured_updates) == 1
    updated_html = captured_updates[0].get("content", "")
    assert '&quot; onerror=&quot;alert(1)' in updated_html
    assert 'onerror="alert(1)"' not in updated_html
    assert '&quot; quote' in updated_html
    assert '&lt;script&gt;' in updated_html
