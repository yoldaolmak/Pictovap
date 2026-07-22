"""Unit tests for the vision_chain multi-provider vision client."""
from __future__ import annotations

import json
import base64
import io
from unittest.mock import patch

import pytest


def test_parse_json_from_text_json_block():
    from pictovap.engine.vision_chain import _parse_json_from_text
    text = '```json\n{"alt": "test", "title": "t"}\n```'
    result = _parse_json_from_text(text)
    assert result["alt"] == "test"


def test_parse_json_from_text_bare_json():
    from pictovap.engine.vision_chain import _parse_json_from_text
    text = 'Some text {"alt": "coast", "title": "Sea"} more text'
    result = _parse_json_from_text(text)
    assert result["alt"] == "coast"


def test_parse_json_from_text_raises_on_no_json():
    from pictovap.engine.vision_chain import _parse_json_from_text
    with pytest.raises(ValueError, match="No JSON found"):
        _parse_json_from_text("no json here at all")


def test_has_any_vision_source_with_gemini_key():
    from pictovap.engine.vision_chain import has_any_vision_source
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key-123"}), \
            patch("pictovap.engine.vision_chain.urllib.request.urlopen", side_effect=OSError):
        assert has_any_vision_source() is True


def test_has_any_vision_source_with_lm_studio_running():
    from pictovap.engine.vision_chain import has_any_vision_source
    with patch.dict("os.environ", {"GEMINI_API_KEY": ""}), \
            patch("pictovap.engine.vision_chain.urllib.request.urlopen"):
        assert has_any_vision_source() is True


def test_has_any_vision_source_false_when_nothing_configured():
    from pictovap.engine.vision_chain import has_any_vision_source
    with patch.dict("os.environ", {"GEMINI_API_KEY": ""}), \
            patch("pictovap.engine.vision_chain.urllib.request.urlopen", side_effect=OSError):
        assert has_any_vision_source() is False


def test_analyze_gemini_flash_raises_without_key():
    from pictovap.engine.vision_chain import _analyze_gemini_flash
    with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
            _analyze_gemini_flash("photo.jpg", "Istanbul", {})


def test_analyze_lm_studio_raises_when_unreachable(tmp_path):
    from pictovap.engine.vision_chain import _analyze_lm_studio
    with patch("pictovap.engine.vision_chain.urllib.request.urlopen", side_effect=OSError("refused")):
        with pytest.raises(RuntimeError, match="not running or unreachable"):
            _analyze_lm_studio("photo.jpg", "Istanbul", {})


def test_lm_studio_uses_template_output_budget(tmp_path):
    from pictovap.engine.vision_chain import _analyze_lm_studio
    from pictovap.vision_templates import MINIMAL

    image = tmp_path / "photo.jpg"
    image.write_bytes(b"jpeg-bytes")
    captured = {}

    class Response:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps(self.payload).encode()

    def fake_urlopen(request, timeout):
        if "models" in request.full_url:
            return Response({"data": [{"id": "local-vision"}]})
        captured.update(json.loads(request.data))
        return Response({"choices": [{"message": {"content": '{"alt":"short"}'}}]})

    with patch("pictovap.engine.vision_chain.urllib.request.urlopen", side_effect=fake_urlopen):
        result = _analyze_lm_studio(str(image), "Istanbul", {}, template=MINIMAL)

    assert result["alt"] == "short"
    assert captured["max_tokens"] == MINIMAL.max_output_tokens


def test_gemini_image_payload_is_downscaled_for_token_budget(tmp_path):
    from PIL import Image

    from pictovap.engine.vision_chain import _image_b64, VISION_MAX_IMAGE_SIDE

    image = tmp_path / "large.jpg"
    Image.new("RGB", (2400, 1600), "white").save(image)

    encoded, mime = _image_b64(str(image), max_side=VISION_MAX_IMAGE_SIDE)
    decoded = Image.open(io.BytesIO(base64.b64decode(encoded)))

    assert mime == "image/jpeg"
    assert max(decoded.size) == VISION_MAX_IMAGE_SIDE


def test_vision_chain_raises_when_all_providers_fail(tmp_path):
    """All providers fail -> RuntimeError listing each failure."""
    from pictovap.engine.vision_chain import analyze_image_vision_chain
    fake_img = tmp_path / "test.jpg"
    fake_img.write_bytes(b"fake")

    with patch("pictovap.engine.vision_chain._analyze_lm_studio", side_effect=RuntimeError("not running")), \
            patch("pictovap.engine.vision_chain._analyze_gemini_flash", side_effect=RuntimeError("no key")):
        with pytest.raises(RuntimeError, match="every vision provider was tried"):
            analyze_image_vision_chain(str(fake_img), location_hint="test", post_context={})


def test_vision_chain_returns_first_success(tmp_path):
    """The first successful provider's result is returned; later ones are skipped."""
    from pictovap.engine.vision_chain import analyze_image_vision_chain
    fake_img = tmp_path / "test.jpg"
    fake_img.write_bytes(b"fake")

    expected = {"alt": "test alt", "title": "T", "caption": "C", "description": "D", "keywords": ["k"]}
    with patch("pictovap.engine.vision_chain._analyze_lm_studio", side_effect=RuntimeError("not running")), \
            patch("pictovap.engine.vision_chain._analyze_gemini_flash", return_value=dict(expected)) as mock_gemini:
        result = analyze_image_vision_chain(str(fake_img), location_hint="test", post_context={})

    assert result["source"] == "gemini_flash"
    assert result["alt"] == "test alt"
    mock_gemini.assert_called_once()


def test_vision_chain_prefers_lm_studio_when_available(tmp_path):
    """LM Studio is tried first; if it succeeds, Gemini is never called."""
    from pictovap.engine.vision_chain import analyze_image_vision_chain
    fake_img = tmp_path / "test.jpg"
    fake_img.write_bytes(b"fake")

    expected = {"alt": "local alt", "title": "T", "caption": "C", "description": "D", "keywords": ["k"]}
    with patch("pictovap.engine.vision_chain._analyze_lm_studio", return_value=dict(expected)), \
            patch("pictovap.engine.vision_chain._analyze_gemini_flash") as mock_gemini:
        result = analyze_image_vision_chain(str(fake_img), location_hint="test", post_context={})

    assert result["source"] == "lm_studio"
    mock_gemini.assert_not_called()
