"""Pictovap Vision Chain — multi-provider vision analysis.

Tries each configured vision provider in order and returns the first
successful result:

  1. LM Studio (local OpenAI-compatible server, no API key, checked first
     since a local request is nearly instant when nothing is running there)
  2. Gemini Flash REST API (GEMINI_API_KEY — free tier via Google AI Studio)

If every provider fails or none is configured, this raises RuntimeError.
There is no silent "basic" fallback here by design — `core.demo_metadata`
is the deterministic, credential-free alternative used by the demo path;
this module is only reached when the caller actually wants vision-backed
metadata and should know if that failed.
"""

from __future__ import annotations

import base64
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict

from pictova.utils.config import env_str, load_project_env
from pictova.vision_templates import TRAVEL_BLOG

load_project_env()


# ── Shared helpers ───────────────────────────────────────────────────────────

def _image_b64(image_path: str, max_side: int = 0) -> tuple[str, str]:
    """Return (base64_str, mime_type). If max_side>0, downsizes via PIL first."""
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


def _parse_json_from_text(text: str) -> Dict:
    """Extract a JSON object from free-form model output."""
    text = text.strip()
    # ```json ... ``` block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if m:
        return json.loads(m.group(1))
    # First { ... }
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        return json.loads(m.group(0))
    raise ValueError(f"No JSON found in response: {text[:200]}")


def _vision_prompt(
    image_path: str,
    location_hint: str,
    post_context: Dict,
    template=None,
) -> str:
    """Build the vision prompt.

    Delegates to the supplied VisionTemplate, or to the built-in TRAVEL_BLOG
    template otherwise. Output language is driven by
    ``post_context["language"]`` — see ``vision_templates.TRAVEL_BLOG``.
    """
    active_template = template or TRAVEL_BLOG
    return active_template.build_prompt(location_hint, post_context)


# ── 1. LM Studio (local, no API key) ─────────────────────────────────────────

def _analyze_lm_studio(
    image_path: str,
    location_hint: str,
    post_context: Dict,
    template=None,
) -> Dict[str, Any]:
    url_models = "http://localhost:1234/v1/models"
    url_chat = "http://localhost:1234/v1/chat/completions"

    try:
        req_models = urllib.request.Request(url_models)
        with urllib.request.urlopen(req_models, timeout=2) as resp:
            models_data = json.loads(resp.read().decode("utf-8"))
            models = models_data.get("data", [])
            if not models:
                raise RuntimeError("No model loaded in LM Studio")
            model_id = models[0]["id"]
    except Exception as e:
        raise RuntimeError(f"LM Studio is not running or unreachable: {e}")

    b64_mime, b64_data = _image_b64(image_path, max_side=1024)
    prompt = _vision_prompt(image_path, location_hint, post_context, template)

    # The target output language is already specified inside `prompt` itself
    # (see vision_templates.TRAVEL_BLOG) — this system message stays
    # deliberately language-neutral.
    system_msg = (
        "You are an image analysis assistant. Describe images objectively, "
        "plainly, and naturally. Reply with raw JSON only, no explanation "
        "or surrounding text."
    )

    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_msg},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{b64_mime};base64,{b64_data}"},
                    },
                ],
            },
        ],
        "temperature": 0.3,
        "max_tokens": 800,
    }

    req = urllib.request.Request(
        url_chat,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        if "does not support image" in err_body or e.code == 400:
            raise RuntimeError(f"LM Studio's loaded model doesn't support images: {err_body[:200]}")
        raise RuntimeError(f"LM Studio API error: {e.code} - {err_body[:200]}")
    except Exception as e:
        raise RuntimeError(f"LM Studio connection error: {e}")

    choice = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    output = choice.strip()
    if not output:
        raise RuntimeError("LM Studio returned an empty response")

    return _parse_json_from_text(output)


# ── 2. Gemini Flash REST API ──────────────────────────────────────────────────

def _analyze_gemini_flash(
    image_path: str,
    location_hint: str,
    post_context: Dict,
    template=None,
) -> Dict[str, Any]:
    api_key = env_str("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    b64, mime = _image_b64(image_path)
    prompt = _vision_prompt(image_path, location_hint, post_context, template)
    model = env_str("GEMINI_VISION_MODEL", "gemini-2.0-flash")

    body = json.dumps({
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": mime, "data": b64}},
                {"text": prompt},
            ]
        }],
        "generationConfig": {"maxOutputTokens": 2048, "temperature": 0.2},
    }).encode()

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )

    # Basic retry with backoff on rate limiting / transient unavailability.
    # This is a single free-tier key; no multi-key rotation here by design —
    # if you're hitting limits regularly, either request a paid quota bump
    # or lower your request volume.
    max_attempts = 4
    data = None
    for attempt in range(max_attempts):
        try:
            req = urllib.request.Request(
                url, data=body, method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < max_attempts - 1:
                wait = 5 * (2 ** attempt)  # 5s, 10s, 20s
                time.sleep(wait)
                continue
            raise RuntimeError(f"Gemini API error {e.code}: {e.reason}") from e

    if data is None:
        raise RuntimeError("Gemini API request failed after retries")

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return _parse_json_from_text(text)


# ── Chain entry point ─────────────────────────────────────────────────────────

def analyze_image_vision_chain(
    image_path: str,
    *,
    location_hint: str = "",
    post_context: Dict | None = None,
    template=None,
) -> Dict[str, Any]:
    """Analyze an image through the vision provider chain.

    Args:
        image_path:    Path to the image file.
        location_hint: Geographic context hint (e.g. "Akyaka").
        post_context:  Dict with ``title``, ``slug``, ``language``, etc.
        template:      Optional :class:`~pictova.vision_templates.VisionTemplate`
                       or template name string (e.g. ``"technical"``).
                       Defaults to the built-in ``travel_blog`` template.

    Returns:
        Dict with ``alt``, ``title``, ``caption``, ``description``,
        ``keywords``, ``source``, and optional ``scene``, ``activity``.

    Raises:
        RuntimeError: when every provider fails or none is configured.

    Example::

        from pictova.engine.vision_chain import analyze_image_vision_chain
        from pictova.vision_templates import TECHNICAL

        meta = analyze_image_vision_chain(
            "photo.webp",
            location_hint="Istanbul",
            template=TECHNICAL,
        )
    """
    if isinstance(template, str):
        from pictova.vision_templates import get_template
        template = get_template(template)
    post_context = post_context or {}
    errors: list[str] = []

    # 1. LM Studio (local; try first since a local check is cheap when it
    # isn't running, and free when it is)
    try:
        result = _analyze_lm_studio(image_path, location_hint, post_context, template=template)
        result["source"] = "lm_studio"
        return result
    except Exception as exc:
        errors.append(f"lm_studio: {exc}")

    # 2. Gemini Flash
    try:
        result = _analyze_gemini_flash(image_path, location_hint, post_context, template=template)
        result["source"] = "gemini_flash"
        return result
    except Exception as exc:
        errors.append(f"gemini_flash: {exc}")

    raise RuntimeError(
        "Image analysis failed — every vision provider was tried:\n"
        + "\n".join(f"  - {e}" for e in errors)
    )


def has_any_vision_source() -> bool:
    """Is at least one vision provider available right now?"""
    try:
        with urllib.request.urlopen("http://localhost:1234/v1/models", timeout=1):
            return True
    except Exception:
        pass
    return bool(env_str("GEMINI_API_KEY", ""))


__all__ = ["analyze_image_vision_chain", "has_any_vision_source"]
