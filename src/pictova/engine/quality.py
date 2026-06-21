"""Quality validation exports."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from src.core.media_quality import (
    BAD_METADATA_TOKENS,
    normalize_text,
    validate_metadata,
    validate_processed_asset,
)


def validate_native_metadata(metadata: Dict[str, Any], post_context: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    title = str(metadata.get("title", "")).strip()
    alt = str(metadata.get("alt", "")).strip()
    caption = str(metadata.get("caption", "")).strip()
    description = str(metadata.get("description", "")).strip()
    post_title = normalize_text(post_context.get("title", ""))

    if len(title) < 8:
        errors.append("title too short")
    if len(alt) < 12:
        errors.append("alt too short")
    if len(caption) < 12:
        errors.append("caption too short")
    if len(description) < 24:
        errors.append("description too short")

    combined = normalize_text(" ".join([title, alt, caption, description]))
    if any(token in combined for token in BAD_METADATA_TOKENS):
        errors.append("metadata contains source junk tokens")

    if post_title and normalize_text(title) == post_title:
        errors.append("title mirrors post title without visual distinction")

    return errors


def quality_gate_native_batch(
    *,
    processed_images: List[str],
    metadata_dict: Dict[str, Dict[str, Any]],
    processed_details: Dict[str, Dict[str, Any]],
    post_context: Dict[str, Any],
) -> Tuple[List[str], Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    approved_files: List[str] = []
    approved_metadata: Dict[str, Dict[str, Any]] = {}
    approved_details: Dict[str, Dict[str, Any]] = {}
    blocked: List[Dict[str, Any]] = []

    for image_file in processed_images:
        metadata = metadata_dict.get(image_file, {})
        process_info = processed_details.get(image_file)
        errors = validate_native_metadata(metadata, post_context)
        errors.extend(validate_processed_asset(metadata, process_info))
        if errors:
            blocked.append({"file": image_file, "errors": errors})
            continue
        approved_files.append(image_file)
        approved_metadata[image_file] = metadata
        approved_details[image_file] = process_info or {}

    return approved_files, approved_metadata, approved_details, blocked


__all__ = [
    "normalize_text",
    "quality_gate_native_batch",
    "validate_metadata",
    "validate_native_metadata",
    "validate_processed_asset",
]
