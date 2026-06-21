#!/usr/bin/env python3
from __future__ import annotations

"""
YO OS Metadata Generator — Semantic alt/title/caption/description
Uses Claude Vision API to analyze images and generate SEO-friendly metadata
"""

import base64
import json
import re
from pathlib import Path
from typing import Dict
import os

from src.utils.config import load_project_env

load_project_env()

BAD_SOURCE_TOKENS = {
    "depositphotos", "xl", "yo", "processed", "final", "image", "img", "jpeg", "jpg", "png", "webp"
}

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class YOMetadataGenerator:
    """Generate semantic metadata with GPT-4 Vision (primary) or Claude Vision (fallback)"""

    def __init__(self, api_key: str = None, use_gpt: bool = True):
        self.use_gpt = use_gpt and OpenAI is not None
        self.use_claude = Anthropic is not None
        self.openai_keys: list[str] = []
        self.openai_models = self._load_openai_models()
        self.claude_models = self._load_claude_models()

        if self.use_gpt:
            primary = api_key or os.environ.get("OPENAI_API_KEY")
            if primary and primary.strip():
                self.openai_keys.append(primary.strip())
            for i in range(2, 5):
                alt_key = os.environ.get(f"OPENAI_API_KEY_{i}")
                if alt_key and alt_key.strip() and alt_key.strip() not in self.openai_keys:
                    self.openai_keys.append(alt_key.strip())
            if not self.openai_keys:
                raise ValueError("No OpenAI API key available")
            self.client = OpenAI(api_key=self.openai_keys[0])
        elif self.use_claude:
            self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        else:
            raise ImportError("Either OpenAI or Anthropic SDK required")

    def _load_openai_models(self) -> list[str]:
        raw = os.environ.get("YO_OPENAI_VISION_MODELS", "").strip()
        if raw:
            return [item.strip() for item in raw.split(",") if item.strip()]
        return ["gpt-4.1", "gpt-4o"]

    def _load_claude_models(self) -> list[str]:
        raw = os.environ.get("YO_CLAUDE_VISION_MODELS", "").strip()
        if raw:
            return [item.strip() for item in raw.split(",") if item.strip()]
        return [
            "claude-sonnet-4-6",
            "claude-haiku-4-5-20251001",
            "claude-3-5-sonnet-20241022",
        ]

    def analyze_image(
        self,
        image_path: str,
        location_hint: str = "",
        post_context: Dict | None = None,
        image_index: int | None = None,
        total_images: int | None = None,
        vision_hints: Dict | None = None,
    ) -> Dict:
        """Analyze image with GPT-4 Vision or Claude Vision

        Args:
            image_path: path to image file
            location_hint: optional hint like "petra" or "istanbul"

        Returns:
            dict with semantic analysis
        """
        image_p = Path(image_path)
        if not image_p.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Read image as base64
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        # Determine media type
        ext = image_p.suffix.lower()
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }
        media_type = media_type_map.get(ext, "image/jpeg")

        prompt = self._build_prompt(
            image_path=image_path,
            location_hint=location_hint,
            post_context=post_context or {},
            image_index=image_index,
            total_images=total_images,
            vision_hints=vision_hints or {},
        )

        try:
            if self.use_gpt:
                result = self._analyze_gpt(image_data, media_type, prompt)
            elif self.use_claude:
                result = self._analyze_claude(image_data, media_type, prompt)
            else:
                result = {
                    "success": False,
                    "image": str(image_path),
                    "error": "No model available",
                }
            if result.get("success"):
                result["analysis"] = normalize_metadata(
                    result.get("analysis", {}),
                    image_path=image_path,
                    location_hint=location_hint,
                    post_context=post_context or {},
                )
            return result
        except Exception as e:
            return {
                "success": False,
                "image": str(image_path),
                "error": str(e),
            }

    def _build_prompt(
        self,
        *,
        image_path: str,
        location_hint: str,
        post_context: Dict,
        image_index: int | None,
        total_images: int | None,
        vision_hints: Dict,
    ) -> str:
        article_title = clean_text(post_context.get("title", ""))
        article_slug = clean_text(post_context.get("slug", ""))
        article_excerpt = clean_text(post_context.get("excerpt", ""), limit=220)
        # Sadece excerpt, title ve focus term kullan — full content çok token
        focus_terms = ", ".join(extract_focus_terms(post_context, location_hint))
        seq = f"{image_index + 1}/{total_images}" if (image_index is not None and total_images) else "?"
        vision_text = format_vision_hints(vision_hints)

        return f"""WordPress medya metadata üret. Sadece JSON döndür.

Bağlam: title={article_title or "?"} | slug={article_slug or "?"} | focus={focus_terms or "?"} | hint={location_hint or "?"} | dosya={Path(image_path).name} | sıra={seq}
{f"Excerpt: {article_excerpt}" if article_excerpt else ""}
{vision_text}

Kurallar: Türkçe. Gördüğünü yaz, uydurma. Lokasyon adını ancak kuvvetli kanıtla yaz. Tekrar spam yapma.
alt≤125 | title≤60 | caption≤180 | description≤300 | keywords 3-6 | evidence 1-4 | confidence 0-1

{{"alt":"...","title":"...","caption":"...","description":"...","keywords":["k1"],"evidence":["kanıt"],"location_tokens":[],"scene_tokens":["sahne"],"confidence":0.8,"warnings":[]}}"""

    def _analyze_gpt(self, image_data: str, media_type: str, prompt: str) -> Dict:
        """Analyze with GPT-4o Vision"""
        last_error = None
        for key in self.openai_keys:
            client = OpenAI(api_key=key)
            for model in self.openai_models:
                try:
                    response = client.chat.completions.create(
                        model=model,
                        max_tokens=400,
                        response_format={"type": "json_object"},
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": prompt,
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{media_type};base64,{image_data}",
                                        },
                                    },
                                ],
                            }
                        ],
                    )

                    response_text = (response.choices[0].message.content or "").strip()
                    metadata = self._parse_metadata_json(response_text)

                    return {
                        "success": True,
                        "source": f"gpt:{model}",
                        "analysis": metadata,
                        "tokens_used": response.usage.prompt_tokens + response.usage.completion_tokens,
                    }
                except Exception as e:
                    last_error = e
                    error_text = str(e).lower()
                    if any(token in error_text for token in ("429", "quota", "billing", "rate limit", "insufficient_quota")):
                        break
                    if any(token in error_text for token in ("model", "not found", "unsupported")):
                        continue
                    if any(token in error_text for token in ("401", "403", "invalid api key", "authentication")):
                        break
                    raise

        raise last_error

    def _analyze_claude(self, image_data: str, media_type: str, prompt: str) -> Dict:
        """Analyze with Claude Vision (fallback)"""
        last_error = None
        for model in self.claude_models:
            try:
                message = self.client.messages.create(
                    model=model,
                    max_tokens=400,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": image_data,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": prompt,
                                }
                            ],
                        }
                    ],
                )

                response_text = message.content[0].text.strip()
                metadata = self._parse_metadata_json(response_text)

                return {
                    "success": True,
                    "source": f"claude:{model}",
                    "analysis": metadata,
                    "tokens_used": message.usage.input_tokens + message.usage.output_tokens,
                }

            except Exception as e:
                last_error = e
                error_text = str(e).lower()
                if any(token in error_text for token in ("model", "not found", "unsupported")):
                    continue
                if any(token in error_text for token in ("429", "quota", "rate limit", "overloaded")):
                    continue
                raise

        raise last_error

    def _parse_metadata_json(self, response_text: str) -> Dict:
        payload = response_text.strip()
        if payload.startswith("```"):
            parts = payload.split("```")
            if len(parts) >= 2:
                payload = parts[1]
                if payload.startswith("json"):
                    payload = payload[4:]
                payload = payload.strip()
        if payload.endswith("```"):
            payload = payload[:-3].strip()
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", payload, re.S)
            if match:
                return json.loads(match.group(0))
            raise

    def generate_filename(self, metadata: Dict, location_hint: str = "") -> str:
        """Generate SEO-friendly filename from metadata"""
        alt = metadata["alt"].lower()
        # Turkish char conversion BEFORE stripping non-ASCII
        # Büyük harf Türkçe → ASCII önce (İ.lower() → i̇ problemi)
        alt = (
            alt.replace("İ", "I").replace("Ş", "S").replace("Ç", "C")
               .replace("Ğ", "G").replace("Ü", "U").replace("Ö", "O")
        )
        alt = alt.lower()
        alt = (
            alt.replace("ş", "s").replace("ç", "c").replace("ğ", "g")
               .replace("ü", "u").replace("ö", "o").replace("ı", "i")
        )
        clean = re.sub(r'[^a-z0-9\s-]', '', alt)
        clean = re.sub(r'\s+', '-', clean.strip())
        clean = re.sub(r'-+', '-', clean)
        if len(clean) > 50:
            clean = clean[:50].rsplit('-', 1)[0]
        return clean or "gorsel"


def generate_metadata_batch(
    image_paths: list,
    location_hint: str = "",
) -> Dict:
    """Generate metadata for multiple images

    Args:
        image_paths: list of file paths
        location_hint: location context for all images

    Returns:
        dict mapping filepath → metadata
    """
    generator = YOMetadataGenerator()
    results = {}

    for i, img_path in enumerate(image_paths, 1):
        print(f"\n[{i}/{len(image_paths)}] Analyzing: {Path(img_path).name}")
        result = generator.analyze_image(img_path, location_hint=location_hint)

        if result["success"]:
            print(f"  ✓ Alt: {result['analysis']['alt'][:50]}...")
            results[img_path] = result["analysis"]
        else:
            print(f"  ✗ Error: {result['error']}")
            results[img_path] = None

    return results


def clean_text(value: str, limit: int = 300) -> str:
    cleaned = re.sub(r"\s+", " ", str(value or "")).strip()
    return cleaned[:limit]


def slug_to_words(value: str) -> str:
    text = str(value or "").replace("-", " ").replace("_", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def sanitize_source_words(value: str) -> str:
    raw = slug_to_words(value)
    tokens = re.findall(r"[a-zA-Z0-9çğıöşüÇĞİÖŞÜ]+", raw)
    cleaned: list[str] = []
    for token in tokens:
        lower = token.lower()
        if lower in BAD_SOURCE_TOKENS:
            continue
        if lower.isdigit():
            continue
        if sum(ch.isdigit() for ch in lower) >= max(2, len(lower) // 2):
            continue
        cleaned.append(token)
    return " ".join(cleaned).strip()


def extract_focus_terms(post_context: Dict, location_hint: str = "") -> list[str]:
    location_hint = sanitize_source_words(location_hint)
    raw = " ".join(
        [
            clean_text(post_context.get("title", ""), limit=120),
            slug_to_words(post_context.get("slug", "")),
            clean_text(location_hint, limit=80),
        ]
    ).lower()
    tokens = re.findall(r"[a-zA-Z0-9çğıöşüÇĞİÖŞÜ]+", raw)
    stopwords = {
        "ve", "ile", "için", "gezi", "rehberi", "en", "bir", "bu", "gibi", "yeri",
        "yerler", "yer", "nasil", "nasıl", "ne", "nerede", "güncel", "detayli", "detaylı",
    }
    seen: list[str] = []
    for token in tokens:
        lower = token.lower()
        if len(lower) < 3 or lower in stopwords or lower in seen:
            continue
        seen.append(lower)
    return seen[:6]


def translate_vision_label(label: str) -> str:
    mapping = {
        "beach": "sahil",
        "coast": "kiyi",
        "sea": "deniz",
        "ocean": "deniz",
        "bay": "koy",
        "island": "ada",
        "boat": "tekne",
        "ship": "tekne",
        "harbor": "liman",
        "port": "liman",
        "temple": "tapinak",
        "pagoda": "pagoda",
        "building": "yapi",
        "city": "sehir",
        "town": "kent",
        "street": "sokak",
        "alley": "sokak",
        "market": "pazar",
        "food": "yemek",
        "dish": "yemek",
        "restaurant": "restoran",
        "bridge": "kopru",
        "river": "nehir",
        "lake": "gol",
        "mountain": "dag",
        "hill": "tepe",
        "forest": "orman",
        "nature": "doga",
        "landscape": "manzara",
        "travel": "gezi",
        "tourism": "seyahat",
        "sky": "gokyuzu",
        "sunset": "gun batimi",
        "sunrise": "gun dogumu",
        "night": "gece",
        "architecture": "mimari",
        "palace": "saray",
        "castle": "kale",
        "park": "park",
        "garden": "bahce",
        "rice": "pirinc",
        "terrace": "teras",
        "person": "insan",
    }
    lower = clean_text(label, limit=40).lower()
    return mapping.get(lower, lower)


def build_vision_assisted_metadata(
    *,
    image_path: str,
    analysis: Dict,
    location_hint: str = "",
    post_context: Dict | None = None,
) -> Dict:
    post_context = post_context or {}
    title = clean_text(post_context.get("title", ""), limit=120)
    excerpt = clean_text(post_context.get("excerpt", ""), limit=220)
    focus_terms = extract_focus_terms(post_context, location_hint)
    labels = [translate_vision_label(item.get("description", "")) for item in analysis.get("labels", [])[:5]]
    labels = [label for label in labels if label and label not in {"seyahat", "gezi"}]
    landmarks = [clean_text(item, limit=40).lower() for item in analysis.get("landmarks", [])[:2] if clean_text(item, limit=40)]
    scene = landmarks[0] if landmarks else (labels[0] if labels else "")
    qualifier = labels[1] if len(labels) > 1 and labels[1] != scene else ""
    visual_phrase = " ".join(part for part in [scene, qualifier] if part).strip()

    if not visual_phrase:
        return build_basic_metadata(image_path=image_path, location_hint=location_hint, post_context=post_context)

    alt = f"{title} {visual_phrase}".strip() if title else visual_phrase
    short_title = " ".join(part for part in [focus_terms[0] if focus_terms else location_hint, scene] if part).strip()
    caption = excerpt or f"{title} içeriğinde öne çıkan {visual_phrase} görünümü"
    description = f"{title} içeriğiyle ilişkili {visual_phrase} görünümü." if title else f"{visual_phrase} görünümü."
    keywords = [kw for kw in [scene, qualifier, *focus_terms[:4], *landmarks] if kw]

    return {
        "alt": clean_text(alt, limit=125),
        "title": clean_text(short_title or scene, limit=60),
        "caption": clean_text(caption, limit=180),
        "description": clean_text(description, limit=300),
        "keywords": keywords[:6],
    }


def format_vision_hints(analysis: Dict | None) -> str:
    analysis = analysis or {}
    labels = [clean_text(item.get("description", ""), limit=40) for item in analysis.get("labels", [])[:5]]
    labels = [label for label in labels if label]
    landmarks = [clean_text(item, limit=40) for item in analysis.get("landmarks", [])[:3] if clean_text(item, limit=40)]
    colors = [item.get("hex", "") for item in analysis.get("colors", [])[:3] if item.get("hex")]
    parts: list[str] = []
    if labels:
        parts.append(f"Vision labels: {', '.join(labels)}")
    if landmarks:
        parts.append(f"Vision landmarks: {', '.join(landmarks)}")
    if colors:
        parts.append(f"Vision colors: {', '.join(colors)}")
    return " | ".join(parts) or "Vision hints: none"


def normalize_metadata(metadata: Dict, *, image_path: str, location_hint: str, post_context: Dict) -> Dict:
    fallback = build_basic_metadata(image_path=image_path, location_hint=location_hint, post_context=post_context)
    normalized = {
        "alt": clean_text(metadata.get("alt", ""), limit=125) or fallback["alt"],
        "title": clean_text(metadata.get("title", ""), limit=60) or fallback["title"],
        "caption": clean_text(metadata.get("caption", ""), limit=180) or fallback["caption"],
        "description": clean_text(metadata.get("description", ""), limit=300) or fallback["description"],
    }
    raw_keywords = metadata.get("keywords", [])
    if isinstance(raw_keywords, str):
        keywords = [part.strip() for part in raw_keywords.split(",") if part.strip()]
    elif isinstance(raw_keywords, list):
        keywords = [clean_text(str(item), limit=40) for item in raw_keywords if clean_text(str(item), limit=40)]
    else:
        keywords = []
    if not keywords:
        keywords = fallback["keywords"]
    normalized["keywords"] = keywords[:6]
    evidence = metadata.get("evidence", [])
    if isinstance(evidence, str):
        evidence = [part.strip() for part in evidence.split(",") if part.strip()]
    elif not isinstance(evidence, list):
        evidence = []
    normalized["_evidence"] = [clean_text(str(item), limit=50).lower() for item in evidence if clean_text(str(item), limit=50)][:5]

    location_tokens = metadata.get("location_tokens", [])
    if isinstance(location_tokens, str):
        location_tokens = [part.strip() for part in location_tokens.split(",") if part.strip()]
    elif not isinstance(location_tokens, list):
        location_tokens = []
    normalized["_location_tokens"] = [clean_text(str(item), limit=50).lower() for item in location_tokens if clean_text(str(item), limit=50)][:3]

    scene_tokens = metadata.get("scene_tokens", [])
    if isinstance(scene_tokens, str):
        scene_tokens = [part.strip() for part in scene_tokens.split(",") if part.strip()]
    elif not isinstance(scene_tokens, list):
        scene_tokens = []
    normalized["_scene_tokens"] = [clean_text(str(item), limit=50).lower() for item in scene_tokens if clean_text(str(item), limit=50)][:4]

    warnings = metadata.get("warnings", [])
    if isinstance(warnings, str):
        warnings = [part.strip() for part in warnings.split(",") if part.strip()]
    elif not isinstance(warnings, list):
        warnings = []
    normalized["_warnings"] = [clean_text(str(item), limit=80) for item in warnings if clean_text(str(item), limit=80)][:4]
    raw_conf = metadata.get("confidence")
    if raw_conf is None:
        # Model didn't return confidence field → treat as neutral, not zero
        normalized["_confidence"] = 0.65
    else:
        try:
            normalized["_confidence"] = max(0.0, min(1.0, float(raw_conf)))
        except (TypeError, ValueError):
            normalized["_confidence"] = 0.0
    return normalized


def build_basic_metadata(*, image_path: str, location_hint: str = "", post_context: Dict | None = None) -> Dict:
    post_context = post_context or {}
    title = clean_text(post_context.get("title", ""), limit=120)
    slug_words = slug_to_words(post_context.get("slug", ""))
    excerpt = clean_text(post_context.get("excerpt", ""), limit=220)
    stem = Path(image_path).stem.replace("_yo", "")
    stem_words = sanitize_source_words(stem)
    focus_terms = extract_focus_terms(post_context, location_hint)
    location_clean = clean_text(sanitize_source_words(location_hint), limit=80)
    primary_focus = title or slug_words or location_clean or "gezi"
    detail_source = stem_words if stem_words and stem_words.lower() not in primary_focus.lower() else ""
    visual_detail = detail_source or ("genel gezi görünümü" if title else "seyahat görünümü")

    alt = f"{primary_focus} {visual_detail}".strip()
    title_parts = [focus_terms[0] if focus_terms else location_clean, detail_source or "gezi gorunumu"]
    title_text = " ".join(part for part in title_parts if part).strip()

    caption = excerpt or f"{primary_focus} içeriğini destekleyen {visual_detail}"
    description = excerpt or f"{primary_focus} odağında kullanılan {visual_detail}"
    keywords = focus_terms or [clean_text(location_clean or detail_source or "gezi", limit=40).lower()]

    return {
        "alt": clean_text(alt, limit=125),
        "title": clean_text(title_text or primary_focus, limit=60),
        "caption": clean_text(caption, limit=180),
        "description": clean_text(description, limit=300),
        "keywords": [kw for kw in keywords if kw][:6],
    }


if __name__ == "__main__":
    # Test
    test_image = Path.home() / "Downloads" / "kalenderis.jpg"
    if test_image.exists():
        gen = YOMetadataGenerator()
        result = gen.analyze_image(str(test_image), location_hint="petra")
        print("\n✅ Metadata generated:")
        import json
        print(json.dumps(result["analysis"], indent=2, ensure_ascii=False))
    else:
        print(f"Test image not found: {test_image}")
