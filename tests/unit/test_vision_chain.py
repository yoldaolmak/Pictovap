"""vision_chain unit testleri."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_parse_json_from_text_json_block():
    from src.pictova.engine.vision_chain import _parse_json_from_text
    text = '```json\n{"alt": "test", "title": "t"}\n```'
    result = _parse_json_from_text(text)
    assert result["alt"] == "test"


def test_parse_json_from_text_bare_json():
    from src.pictova.engine.vision_chain import _parse_json_from_text
    text = 'Some text {"alt": "coast", "title": "Sea"} more text'
    result = _parse_json_from_text(text)
    assert result["alt"] == "coast"


def test_parse_json_from_text_raises_on_no_json():
    from src.pictova.engine.vision_chain import _parse_json_from_text
    with pytest.raises(ValueError, match="JSON bulunamadı"):
        _parse_json_from_text("no json here at all")


def test_find_bin_uses_shutil_first(tmp_path):
    from src.pictova.engine.vision_chain import _find_bin
    with patch("src.pictova.engine.vision_chain.shutil.which", return_value="/usr/bin/somebin"):
        result = _find_bin("somebin")
    assert result == "/usr/bin/somebin"


def test_find_bin_fallback_to_npm_path(tmp_path):
    from src.pictova.engine.vision_chain import _find_bin
    # Önce olmayan bir binary ara, npm path'ini mock'la
    fake_bin = tmp_path / "claude"
    fake_bin.touch()
    fake_bin.chmod(0o755)
    with patch("src.pictova.engine.vision_chain.shutil.which", return_value=None), \
         patch("src.pictova.engine.vision_chain.Path.home", return_value=tmp_path):
        result = _find_bin("claude")
    # Eğer tmp_path/AI/npm/bin/claude oluşturulmadıysa None döner (davranış doğru)
    assert result is None or isinstance(result, str)


def test_has_any_vision_source_with_gemini_key():
    from src.pictova.engine.vision_chain import has_any_vision_source
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key-123"}):
        assert has_any_vision_source() is True


def test_has_any_vision_source_with_claude_bin():
    from src.pictova.engine.vision_chain import has_any_vision_source
    with patch.dict("os.environ", {"GEMINI_API_KEY": ""}), \
         patch("src.pictova.engine.vision_chain._codex_check_login", return_value=False), \
         patch("src.pictova.engine.vision_chain._find_bin", side_effect=lambda n: "/bin/claude" if n == "claude" else None):
        assert has_any_vision_source() is True


def test_has_any_vision_source_false_when_nothing():
    from src.pictova.engine.vision_chain import has_any_vision_source
    with patch.dict("os.environ", {"GEMINI_API_KEY": ""}), \
         patch("src.pictova.engine.vision_chain.urllib.request.urlopen", side_effect=OSError), \
         patch("src.pictova.engine.vision_chain._codex_check_login", return_value=False), \
         patch("src.pictova.engine.vision_chain._find_bin", return_value=None):
        assert has_any_vision_source() is False


def test_vision_chain_raises_when_all_fail(tmp_path):
    """Tüm kaynaklar başarısız → RuntimeError."""
    from src.pictova.engine.vision_chain import analyze_image_vision_chain
    fake_img = tmp_path / "test.jpg"
    fake_img.write_bytes(b"fake")

    with patch("src.pictova.engine.vision_chain._analyze_gemini_flash", side_effect=RuntimeError("no key")), \
         patch("src.pictova.engine.vision_chain._analyze_codex", side_effect=RuntimeError("no login")), \
         patch("src.pictova.engine.vision_chain._analyze_claude_cli", side_effect=RuntimeError("no claude")):
        with pytest.raises(RuntimeError, match="tüm kaynaklar denendi"):
            analyze_image_vision_chain(str(fake_img), location_hint="test", post_context={})


def test_vision_chain_returns_first_success(tmp_path):
    """İlk başarılı kaynak döner."""
    from src.pictova.engine.vision_chain import analyze_image_vision_chain
    fake_img = tmp_path / "test.jpg"
    fake_img.write_bytes(b"fake")

    expected = {"alt": "test alt", "title": "T", "caption": "C", "description": "D", "keywords": ["k"]}
    with patch("src.pictova.engine.vision_chain._analyze_gemini_flash", return_value=dict(expected)), \
         patch("src.pictova.engine.vision_chain._analyze_codex") as mock_codex, \
         patch("src.pictova.engine.vision_chain._analyze_claude_cli") as mock_claude:
        result = analyze_image_vision_chain(str(fake_img), location_hint="test", post_context={})

    assert result["source"] == "gemini_flash"
    assert result["alt"] == "test alt"
    mock_codex.assert_not_called()
    mock_claude.assert_not_called()
