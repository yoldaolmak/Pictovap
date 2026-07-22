"""
Vision template system for Pictovap.

Developers can define custom prompt templates to control metadata tone,
language, and field structure. Templates can be passed to
``analyze_image_vision_chain`` via the ``template`` parameter.

Built-in templates are provided as constants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict

# ISO 639-1 code -> English display name, used to tell the model which
# natural language to write the generated fields in. Any code not listed
# here is passed through as-is (most vision models understand ISO codes
# and common language names directly).
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "tr": "Turkish",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "ru": "Russian",
    "ar": "Arabic",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
}


def language_name(code: str | None) -> str:
    """Return the English display name for an ISO 639-1 language code.

    Falls back to the code itself (or "English") when the code is unknown,
    so unrecognized codes still degrade gracefully instead of raising.
    """
    if not code:
        return "English"
    return LANGUAGE_NAMES.get(code.lower(), code)


@dataclass
class VisionTemplate:
    """A custom vision prompt template.

    Args:
        name:        Unique identifier for the template.
        description: Human-readable summary of this template's purpose.
        prompt_fn:   Callable that receives ``(location_hint, post_context)``
                     and returns the prompt string to send to the LLM.
        fields:      Expected output JSON keys (used for response validation).
        max_output_tokens: Upper bound passed to the configured vision provider.

    Example::

        from pictovap.vision_templates import VisionTemplate

        my_template = VisionTemplate(
            name="technical",
            description="Strict technical image description, no creative language.",
            prompt_fn=lambda loc, ctx: (
                f"Analyze this image objectively. Location: {loc or 'unknown'}.\\n"
                "Return ONLY JSON: {\"alt\":\"...\",\"title\":\"...\",\"description\":\"...\","
                "\"keywords\":[],\"scene\":\"...\",\"activity\":\"...\",\"story_score\":0.5}"
            ),
        )
    """

    name: str
    description: str
    prompt_fn: Callable[[str, Dict[str, Any]], str]
    fields: list[str] = field(default_factory=lambda: [
        "alt", "title", "caption", "description", "summary",
        "keywords", "people", "scene", "activity", "story_score",
    ])
    max_output_tokens: int = 512

    def __post_init__(self) -> None:
        if not isinstance(self.max_output_tokens, int) or not 64 <= self.max_output_tokens <= 4096:
            raise ValueError("max_output_tokens must be an integer between 64 and 4096")

    def build_prompt(self, location_hint: str, post_context: Dict[str, Any]) -> str:
        """Render the prompt string for this template."""
        return self.prompt_fn(location_hint, post_context)


# ── Built-in templates ────────────────────────────────────────────────────────

def _travel_blog_prompt(location_hint: str, post_context: Dict[str, Any]) -> str:
    """Default Pictovap travel blog template.

    Output language is driven by ``post_context["language"]`` (an ISO 639-1
    code, e.g. "en", "tr", "fr"). Defaults to English when not provided, so a
    request from Turkey can ask for Turkish output, a request from France for
    French, and so on, without any per-language hardcoding here.
    """
    title = str(post_context.get("title") or "").strip()
    location_ctx = location_hint or title or ""
    apple_labels = post_context.get("apple_labels") or []
    apple_labels_ctx = ", ".join(apple_labels) if apple_labels else ""
    lang = language_name(post_context.get("language"))
    return (
        f"Analyze the image in the context of a travel blog post and return ONLY JSON.\n"
        f"Context: Location={location_ctx or '?'}, Apple_Labels={apple_labels_ctx or '?'}\n\n"
        f"Write all natural-language fields (alt, title, caption, description, summary, keywords) "
        f"in {lang}.\n\n"
        f"Rules:\n"
        f"- alt: plain visual description for screen readers/accessibility ({lang}, max 120 chars)\n"
        f"- title: SEO title including location and subject ({lang}, max 60 chars)\n"
        f"- caption: natural, authentic caption for a human reader ({lang}, max 150 chars)\n"
        f"- description: rich description combining visual detail with location context "
        f"({lang}, max 250 chars)\n"
        f"- summary: one-sentence summary ({lang}, max 120 chars)\n"
        f"- keywords: 3-5 keywords ({lang})\n"
        f"- scene/activity: category and activity (English)\n"
        f"- story_score: travel value (0.0 - 1.0)\n\n"
        f"{{\"alt\":\"...\",\"title\":\"...\",\"caption\":\"...\",\"description\":\"...\","
        f"\"summary\":\"...\",\"keywords\":[],\"people\":[],\"scene\":\"...\","
        f"\"activity\":\"...\",\"story_score\":0.8}}"
    )


def _technical_prompt(location_hint: str, post_context: Dict[str, Any]) -> str:
    """Strict technical analysis — no creative language, English output."""
    loc = location_hint or post_context.get("title") or "unknown location"
    return (
        f"Analyze this image objectively and technically. Location context: {loc}.\n"
        "Return ONLY a JSON object. Fields:\n"
        "- alt: precise visual description for screen readers (English, max 120 chars)\n"
        "- title: concise SEO title with subject and location (English, max 60 chars)\n"
        "- caption: one factual sentence about the scene (English, max 100 chars)\n"
        "- description: technical description of composition, lighting, subjects (English, max 250 chars)\n"
        "- summary: single sentence summary (English)\n"
        "- keywords: 3-5 descriptive keywords (English)\n"
        "- scene/activity: scene type and activity (English)\n"
        "- story_score: visual impact score 0.0-1.0\n\n"
        "{\"alt\":\"...\",\"title\":\"...\",\"caption\":\"...\",\"description\":\"...\","
        "\"summary\":\"...\",\"keywords\":[],\"people\":[],\"scene\":\"...\","
        "\"activity\":\"...\",\"story_score\":0.5}"
    )


def _minimal_alt_only_prompt(location_hint: str, post_context: Dict[str, Any]) -> str:
    """Ultra-minimal — only generates alt text (fast, low-token)."""
    loc = location_hint or post_context.get("title") or "scene"
    return (
        f"Describe this image in one short sentence for a screen reader. Context: {loc}.\n"
        "Return ONLY JSON: {\"alt\":\"...\",\"title\":\"\",\"caption\":\"\","
        "\"description\":\"\",\"summary\":\"\",\"keywords\":[],\"people\":[],"
        "\"scene\":\"photo\",\"activity\":\"photography\",\"story_score\":0.5}"
    )


def _ecommerce_prompt(location_hint: str, post_context: Dict[str, Any]) -> str:
    """E-commerce product focus — keyword-rich, conversion-oriented, English."""
    product = location_hint or post_context.get("title") or "product"
    return (
        f"You are an e-commerce SEO copywriter. Analyze this product image. Product: {product}.\n"
        "Return ONLY JSON with these fields:\n"
        "- alt: keyword-rich accessibility description (English, max 125 chars)\n"
        "- title: SEO product title (English, max 70 chars, include product name)\n"
        "- caption: conversion-focused marketing caption (English, max 150 chars)\n"
        "- description: detailed product visual description for listings (English, max 300 chars)\n"
        "- summary: one-line product teaser (English)\n"
        "- keywords: 5-8 SEO keywords including product attributes\n"
        "- scene: 'product'\n- activity: 'ecommerce'\n- story_score: 0.7\n\n"
        "{\"alt\":\"...\",\"title\":\"...\",\"caption\":\"...\",\"description\":\"...\","
        "\"summary\":\"...\",\"keywords\":[],\"people\":[],\"scene\":\"product\","
        "\"activity\":\"ecommerce\",\"story_score\":0.7}"
    )


# ── Template registry ─────────────────────────────────────────────────────────

TRAVEL_BLOG = VisionTemplate(
    name="travel_blog",
    description="Default Pictovap template — travel blog SEO, language-aware output.",
    prompt_fn=_travel_blog_prompt,
    max_output_tokens=512,
)

TECHNICAL = VisionTemplate(
    name="technical",
    description="Strict technical analysis — English output, no creative language.",
    prompt_fn=_technical_prompt,
    max_output_tokens=384,
)

MINIMAL = VisionTemplate(
    name="minimal",
    description="Alt-text only — ultra-fast, minimal token usage.",
    prompt_fn=_minimal_alt_only_prompt,
    max_output_tokens=128,
)

ECOMMERCE = VisionTemplate(
    name="ecommerce",
    description="E-commerce focused — keyword-rich, conversion-oriented, English.",
    prompt_fn=_ecommerce_prompt,
    max_output_tokens=512,
)

_REGISTRY: dict[str, VisionTemplate] = {
    t.name: t for t in [TRAVEL_BLOG, TECHNICAL, MINIMAL, ECOMMERCE]
}


def get_template(name: str) -> VisionTemplate:
    """Look up a built-in template by name.

    Raises:
        KeyError: if the template name is not registered.
    """
    if name not in _REGISTRY:
        available = ", ".join(_REGISTRY)
        raise KeyError(f"Unknown template '{name}'. Available: {available}")
    return _REGISTRY[name]


def register_template(template: VisionTemplate) -> None:
    """Register a custom template globally so it can be used by name.

    Example::

        register_template(VisionTemplate(
            name="my_template",
            description="My custom prompt",
            prompt_fn=lambda loc, ctx: f"Describe image at {loc}. Return JSON...",
        ))
    """
    _REGISTRY[template.name] = template


__all__ = [
    "VisionTemplate",
    "TRAVEL_BLOG",
    "TECHNICAL",
    "MINIMAL",
    "ECOMMERCE",
    "get_template",
    "register_template",
]
