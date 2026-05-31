from __future__ import annotations

import re
from pathlib import Path
from typing import Dict


BAD_METADATA_TOKENS = {"depositphotos", "xl", "processed", "yo"}
ALLOWED_SIZES = {(1200, 750), (1200, 1600), (1200, 1200)}
GENERIC_ANCHORS = {
    "vietnam", "gezi", "gezilecek", "rehberi", "rota", "deneyimler", "seyahat",
    "landmark", "travel", "tourism", "image", "photo", "view", "manzara",
    "scene", "destination", "place", "city", "town", "country", "nature",
    "outdoor", "person", "people", "woman", "man",
}
ANCHOR_EQUIVALENTS = {
    "train": {"train", "tren", "ray", "raylari", "rayları", "rail", "railway"},
    "street": {"street", "sokak", "alley", "cadde"},
    "market": {"market", "pazar", "bazaar", "çarşı", "carsi"},
    "boat": {"boat", "tekne", "gemi", "kayik", "kayık", "ship"},
    "bay": {"bay", "koy", "körfez", "korfez"},
    "limestone": {"limestone", "kirectasi", "kireçtaşı", "karst", "kayalik", "kayalık"},
    "temple": {"temple", "tapinak", "tapınak", "pagoda"},
    "pagoda": {"pagoda", "tapinak", "tapınak"},
    "river": {"river", "nehir", "cay", "çay"},
    "bridge": {"bridge", "kopru", "köprü"},
    "tourist": {"tourist", "turist", "visitors", "ziyaretci", "ziyaretçi"},
    "people": {"people", "insan", "yerel", "halk"},
    "building": {"building", "bina", "ev", "konut", "mimari"},
    "green": {"green", "yesil", "yeşil", "ormanlik", "ormanlık", "tropik"},
    "tour": {"tour", "tur", "trip", "gezi"},
    "temple-complex": {"temple", "tapinak", "tapınak", "pagoda", "kompleks", "complex"},
    "bay-view": {"bay", "koy", "körfez", "korfez", "manzara", "view"},
    "river-tour": {"river", "nehir", "tur", "tour", "tekne", "boat"},
    "train-street": {"train", "tren", "street", "sokak", "ray", "railway"},
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _anchor_tokens_from_text(value: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9çğıöşü]+", normalize_text(value))
    return [
        token for token in tokens
        if len(token) >= 4 and token not in BAD_METADATA_TOKENS and token not in GENERIC_ANCHORS
    ]


def _contains_bad_token(value: str) -> bool:
    tokens = re.findall(r"[a-z0-9çğıöşü]+", normalize_text(value))
    return any(token in BAD_METADATA_TOKENS for token in tokens)


def _expand_anchor_tokens(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for token in list(tokens):
        for variants in ANCHOR_EQUIVALENTS.values():
            if token in variants:
                expanded.update(variants)
    return expanded


def _phrase_supported(value: str, anchors: list[str]) -> bool:
    phrase_tokens = _expand_anchor_tokens(set(_anchor_tokens_from_text(value)))
    if not phrase_tokens:
        return False
    anchor_set = _expand_anchor_tokens(set(anchors))
    overlap = phrase_tokens & anchor_set
    if len(overlap) >= 2:
        return True
    if overlap and len(phrase_tokens) <= 2:
        return True
    return False


def _collect_semantic_anchors(metadata: Dict) -> list[str]:
    anchors: list[str] = []
    seen: set[str] = set()

    source_embedded = metadata.get("_source_embedded", {})
    if isinstance(source_embedded, dict):
        for token in _anchor_tokens_from_text(source_embedded.get("description", "")):
            if token not in seen:
                seen.add(token)
                anchors.append(token)

    vision_hints = metadata.get("_vision_hints", {})
    if isinstance(vision_hints, dict):
        for item in vision_hints.get("labels", [])[:8]:
            label = item.get("description", "") if isinstance(item, dict) else str(item)
            for token in _expand_anchor_tokens(set(_anchor_tokens_from_text(label))):
                if token not in seen:
                    seen.add(token)
                    anchors.append(token)
        for item in vision_hints.get("landmarks", [])[:4]:
            for token in _expand_anchor_tokens(set(_anchor_tokens_from_text(item))):
                if token not in seen:
                    seen.add(token)
                    anchors.append(token)

    for item in metadata.get("_location_tokens", [])[:3]:
        for token in _expand_anchor_tokens(set(_anchor_tokens_from_text(item))):
            if token not in seen:
                seen.add(token)
                anchors.append(token)

    for item in metadata.get("_scene_tokens", [])[:4]:
        for token in _expand_anchor_tokens(set(_anchor_tokens_from_text(item))):
            if token not in seen:
                seen.add(token)
                anchors.append(token)

    return anchors[:8]


def _tokenize_phrase(value: str) -> set[str]:
    return _expand_anchor_tokens(set(_anchor_tokens_from_text(value)))


def _has_anchor_support(value: str, anchors: list[str]) -> bool:
    phrase_tokens = _tokenize_phrase(value)
    if not phrase_tokens:
        return False
    anchor_set = _expand_anchor_tokens(set(anchors))
    return bool(phrase_tokens & anchor_set)


def validate_metadata(metadata: Dict, post_context: Dict, *, duplicate_title: bool = False) -> list[str]:
    errors: list[str] = []
    title = normalize_text(metadata.get("title", ""))
    alt = normalize_text(metadata.get("alt", ""))
    caption = normalize_text(metadata.get("caption", ""))
    description = normalize_text(metadata.get("description", ""))
    post_title = normalize_text(post_context.get("title", ""))
    source = normalize_text(metadata.get("_source", ""))
    anchors = _collect_semantic_anchors(metadata)
    evidence = [normalize_text(item) for item in metadata.get("_evidence", []) if normalize_text(item)]
    location_tokens = [normalize_text(item) for item in metadata.get("_location_tokens", []) if normalize_text(item)]
    scene_tokens = [normalize_text(item) for item in metadata.get("_scene_tokens", []) if normalize_text(item)]
    confidence = float(metadata.get("_confidence", 0) or 0)
    warnings = [normalize_text(item) for item in metadata.get("_warnings", []) if normalize_text(item)]

    if len(title) < 8:
        errors.append("title too short")
    if len(alt) < 12:
        errors.append("alt too short")
    if len(caption) < 12:
        errors.append("caption too short")
    if len(description) < 24:
        errors.append("description too short")

    combined = " ".join([title, alt, caption, description])
    if _contains_bad_token(combined):
        errors.append("metadata contains source junk tokens")

    if post_title and title == post_title:
        errors.append("title mirrors post title without visual distinction")
    if post_title and alt.startswith(post_title):
        extra = alt.replace(post_title, "", 1).strip()
        if len(extra.split()) < 2:
            errors.append("alt lacks visual detail beyond post title")

    if duplicate_title:
        errors.append("duplicate image title in same batch")
    if source == "fallback":
        errors.append("metadata is fallback, not vision verified")
    if metadata.get("embedded") is not True:
        errors.append("metadata not embedded into image")
    if not source.startswith("gpt") and not source.startswith("claude"):
        errors.append("metadata source is not semantic model output")
    if confidence < 0.55:
        errors.append("metadata confidence too low")
    if not evidence:
        errors.append("missing semantic evidence list")
    if len(warnings) >= 2:
        errors.append("model reported repeated semantic uncertainty")
    if not anchors:
        if confidence < 0.82 or location_tokens:
            errors.append("no verified semantic anchors available")
    else:
        combined_tokens = _tokenize_phrase(combined)
        anchor_hits = len(combined_tokens & _expand_anchor_tokens(set(anchors)))
        if anchor_hits == 0:
            errors.append("metadata does not reflect verified photo anchors")
        if not any(_phrase_supported(item, anchors) for item in evidence):
            errors.append("semantic evidence is not supported by verified anchors")
        if location_tokens and not any(_phrase_supported(item, anchors) for item in location_tokens):
            errors.append("metadata location is not supported by verified anchors")
        if scene_tokens and not any(_phrase_supported(item, anchors) for item in scene_tokens):
            errors.append("metadata scene is not supported by verified anchors")
        if location_tokens and not any(token in combined for token in location_tokens):
            errors.append("verified location missing from metadata text")
        if scene_tokens and not any(token in combined for token in scene_tokens):
            errors.append("verified scene missing from metadata text")

    return errors


def validate_processed_asset(meta: Dict, process_info: Dict | None) -> list[str]:
    errors: list[str] = []
    if process_info is None:
        return ["missing process info"]
    final_size = tuple(process_info.get("final_size", ()))
    if final_size not in ALLOWED_SIZES:
        errors.append("non-standard crop size")
    brightness = float(process_info.get("brightness", 0))
    saturation = float(process_info.get("saturation", 0))
    contrast = float(process_info.get("contrast", 0))
    color_temp = float(process_info.get("color_temp", 0))
    file_size_kb = float(process_info.get("file_size_kb", 0))
    if not (0.22 <= brightness <= 0.78):
        errors.append("brightness out of editorial range")
    if not (0.12 <= saturation <= 0.62):
        errors.append("saturation out of editorial range")
    if not (0.10 <= contrast <= 0.30):
        errors.append("contrast out of editorial range")
    if not (-0.12 <= color_temp <= 0.12):
        errors.append("color temperature inconsistent")
    if file_size_kb <= 60:
        errors.append("file too compressed")
    if file_size_kb >= 900:
        errors.append("file too heavy")
    return errors
