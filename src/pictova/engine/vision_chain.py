"""Pictova Vision Chain — görsel analiz öncelik zinciri.

Öncelik (asla basic fallback yok):
  1. Gemini Flash REST (GEMINI_API_KEY — Google AI Studio, ücretsiz)
  2. Codex CLI web login  (codex exec --ephemeral --yolo, ~/.codex/auth.json)
  3. Claude CLI web login (claude --print --allowedTools Read)

Herhangi biri başarılı → döner.
Hepsi başarısız → RuntimeError (basic fallback YOK).
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict


# ── Ortak yardımcılar ────────────────────────────────────────────────────────

def _image_b64(image_path: str, max_side: int = 0) -> tuple[str, str]:
    """(base64_str, mime_type). max_side>0 ise PIL ile thumbnail alır."""
    import io
    p = Path(image_path)
    mime = "image/jpeg"
    if max_side > 0:
        try:
            from PIL import Image as _PIL
            img = _PIL.open(str(p)).convert("RGB")
            img.thumbnail((max_side, max_side))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=70)
            return base64.b64encode(buf.getvalue()).decode(), mime
        except Exception:
            pass
    ext = p.suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode(), mime


def _strip_ansi(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*m|\x1b\[?[0-9;]*[a-zA-Z]', '', text)


def _parse_json_from_text(text: str) -> Dict:
    """JSON bloğunu metinden çıkar."""
    text = text.strip()
    # ```json ... ``` bloğu
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if m:
        return json.loads(m.group(1))
    # İlk { ... }
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        return json.loads(m.group(0))
    raise ValueError(f"JSON bulunamadı: {text[:200]}")


def _vision_prompt(image_path: str, location_hint: str, post_context: Dict) -> str:
    title = str(post_context.get("title") or "").strip()
    slug = str(post_context.get("slug") or "").strip()
    return (
        f"WordPress medya metadata üret. SADECE JSON döndür, başka metin yok.\n\n"
        f"Bağlam: title={title or '?'} | slug={slug or '?'} | hint={location_hint or '?'}\n\n"
        f"Kurallar:\n"
        f"- Gördüğünü yaz, uydurma\n"
        f"- alt: İngilizce, SEO uyumlu, Türkçe harf YASAK, numara YASAK, max 125 char\n"
        f"- title: İngilizce, SEO uyumlu, Türkçe harf YASAK, numara YASAK, max 60 char\n"
        f"- caption: Türkçe olabilir, max 180 char\n"
        f"- description: Türkçe olabilir, max 300 char\n"
        f"- keywords: 3-6 İngilizce kelime, array\n\n"
        f"{{\"alt\":\"...\",\"title\":\"...\",\"caption\":\"...\","
        f"\"description\":\"...\",\"keywords\":[\"k1\",\"k2\"]}}"
    )


# ── 1. Gemini Flash REST API ─────────────────────────────────────────────────

def _analyze_gemini_flash(
    image_path: str,
    location_hint: str,
    post_context: Dict,
) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY yok")

    b64, mime = _image_b64(image_path)
    prompt = _vision_prompt(image_path, location_hint, post_context)
    model = os.environ.get("GEMINI_VISION_MODEL", "gemini-2.0-flash")

    body = json.dumps({
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": mime, "data": b64}},
                {"text": prompt},
            ]
        }],
        "generationConfig": {"maxOutputTokens": 512, "temperature": 0.2},
    }).encode()

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return _parse_json_from_text(text)


# ── 2. Codex CLI web login ───────────────────────────────────────────────────

def _codex_check_login() -> bool:
    auth = Path.home() / ".codex" / "auth.json"
    if not auth.exists():
        return False
    try:
        d = json.loads(auth.read_text())
        t = d.get("tokens", {})
        return bool(t.get("access_token") or t.get("id_token"))
    except Exception:
        return False


def _find_bin(name: str) -> str | None:
    """shutil.which + bilinen npm prefix konumları."""
    found = shutil.which(name)
    if found:
        return found
    candidates = [
        Path.home() / "AI" / "npm" / "bin" / name,
        Path("/usr/local/bin") / name,
        Path("/opt/homebrew/bin") / name,
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def _analyze_codex(
    image_path: str,
    location_hint: str,
    post_context: Dict,
) -> Dict[str, Any]:
    if not _codex_check_login():
        raise RuntimeError("Codex oturumu yok — terminalde: codex login")

    codex_bin = _find_bin("codex")
    if not codex_bin:
        raise RuntimeError("codex CLI bulunamadı")

    prompt_text = _vision_prompt(image_path, location_hint, post_context)
    full_prompt = (
        f"Analyze the image file at path: {image_path}\n\n"
        f"{prompt_text}"
    )

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as of:
        out_path = of.name

    try:
        result = subprocess.run(
            [codex_bin, "exec", "--yolo", "--skip-git-repo-check", "-o", out_path, "-"],
            input=full_prompt,
            text=True, check=False,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            timeout=180,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Codex rc={result.returncode}: {(result.stderr or '')[-500:]}")
        answer = Path(out_path).read_text(encoding="utf-8").strip()
    finally:
        try:
            os.unlink(out_path)
        except OSError:
            pass

    if not answer:
        raise RuntimeError("Codex boş yanıt döndü")
    return _parse_json_from_text(answer)


# ── 3. Claude CLI web login ──────────────────────────────────────────────────

def _analyze_claude_cli(
    image_path: str,
    location_hint: str,
    post_context: Dict,
) -> Dict[str, Any]:
    claude_bin = _find_bin("claude")
    if not claude_bin:
        raise RuntimeError("claude CLI bulunamadı")

    prompt = (
        f"Read the image at: {image_path}\n\n"
        + _vision_prompt(image_path, location_hint, post_context)
    )

    result = subprocess.run(
        [claude_bin, "--print", "--allowedTools", "Read", "--dangerously-skip-permissions",
         "--model", "claude-haiku-4-5-20251001"],
        input=prompt, text=True, check=False,
        capture_output=True, timeout=120,
    )
    output = _strip_ansi((result.stdout or "").strip())
    if result.returncode != 0 or not output:
        raise RuntimeError(f"Claude CLI rc={result.returncode}: {(result.stderr or '')[-300:]}")
    return _parse_json_from_text(output)


# ── Ana zincir ────────────────────────────────────────────────────────────────

def analyze_image_vision_chain(
    image_path: str,
    *,
    location_hint: str = "",
    post_context: Dict | None = None,
) -> Dict[str, Any]:
    """Öncelik zinciri ile görsel analizi. Basic fallback YOK.

    Döner: {"alt":..., "title":..., "caption":..., "description":..., "keywords":[...], "source":"..."}
    Hepsi başarısız → RuntimeError.
    """
    post_context = post_context or {}
    errors: list[str] = []

    # 1. Gemini Flash
    try:
        result = _analyze_gemini_flash(image_path, location_hint, post_context)
        result["source"] = "gemini_flash"
        return result
    except Exception as exc:
        errors.append(f"gemini_flash: {exc}")

    # 2. Codex CLI
    try:
        result = _analyze_codex(image_path, location_hint, post_context)
        result["source"] = "codex_cli"
        return result
    except Exception as exc:
        errors.append(f"codex_cli: {exc}")

    # 3. Claude CLI
    try:
        result = _analyze_claude_cli(image_path, location_hint, post_context)
        result["source"] = "claude_cli"
        return result
    except Exception as exc:
        errors.append(f"claude_cli: {exc}")

    raise RuntimeError(
        "Görsel analizi başarısız — tüm kaynaklar denendi:\n"
        + "\n".join(f"  • {e}" for e in errors)
    )


def has_any_vision_source() -> bool:
    """En az bir kaynak kullanılabilir mi?"""
    if os.environ.get("GEMINI_API_KEY", "").strip():
        return True
    if _codex_check_login() and _find_bin("codex"):
        return True
    if _find_bin("claude"):
        return True
    return False


def download_icloud_photo(uuid: str, dest_dir: str | None = None) -> str:
    """iCloud fotoğrafı UUID ile indir, lokal path döner.

    python3.11 ve osxphotos gerektirir.
    dest_dir yoksa /tmp/pictova_icloud/ kullanılır.
    """
    import subprocess as _sp
    import tempfile as _tmp

    dest = Path(dest_dir) if dest_dir else Path(_tmp.gettempdir()) / "pictova_icloud"
    dest.mkdir(parents=True, exist_ok=True)

    script = (
        f"import osxphotos, sys\n"
        f"db = osxphotos.PhotosDB()\n"
        f"res = db.query(osxphotos.QueryOptions(uuid=['{uuid}']))\n"
        f"if not res: sys.exit(1)\n"
        f"exported = res[0].export('{dest}', use_photos_export=True, overwrite=True, timeout=300)\n"
        f"print(exported[0] if exported else '')\n"
    )

    py311 = shutil.which("python3.11") or "python3.11"
    result = _sp.run([py311, "-c", script], capture_output=True, text=True, timeout=360)
    path = result.stdout.strip()
    if result.returncode != 0 or not path:
        raise RuntimeError(
            f"iCloud indirme başarısız (uuid={uuid}): {result.stderr[-300:]}"
        )
    return path


__all__ = ["analyze_image_vision_chain", "has_any_vision_source", "download_icloud_photo"]
