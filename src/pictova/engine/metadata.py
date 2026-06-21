"""Metadata generation exports."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.core.metadata_generator import YOMetadataGenerator, build_basic_metadata


def build_basic_metadata_map(
    image_files: List[str],
    *,
    location_hint: str = "",
    post_context: Dict[str, Any] | None = None,
) -> Dict[str, Dict[str, Any]]:
    post_context = post_context or {}
    metadata_dict: Dict[str, Dict[str, Any]] = {}
    for image_file in image_files:
        metadata = build_basic_metadata(
            image_path=image_file,
            location_hint=location_hint,
            post_context=post_context,
        )
        metadata["heading"] = post_context.get("title", "") or Path(image_file).stem
        metadata["heading_level"] = 2
        metadata_dict[image_file] = metadata
    return metadata_dict


def _has_vision_credentials() -> bool:
    return bool(
        (os.environ.get("OPENAI_API_KEY") or "").strip()
        or (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    )


def build_native_metadata_map(
    image_files: List[str],
    *,
    location_hint: str = "",
    post_context: Dict[str, Any] | None = None,
    mode: str = "auto",
) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    post_context = post_context or {}
    metadata_dict = build_basic_metadata_map(
        image_files,
        location_hint=location_hint,
        post_context=post_context,
    )

    normalized_mode = str(mode or "auto").strip().lower()
    if normalized_mode == "basic":
        return metadata_dict, ["basic metadata fallback only"]

    if normalized_mode not in {"auto", "vision"}:
        return metadata_dict, [f"unknown metadata mode: {normalized_mode}; basic fallback used"]

    if not _has_vision_credentials():
        return metadata_dict, ["basic metadata fallback only"]

    try:
        generator = YOMetadataGenerator(use_gpt=bool((os.environ.get("OPENAI_API_KEY") or "").strip()))
    except Exception as exc:
        return metadata_dict, [f"basic metadata fallback only: {exc}"]

    warnings: List[str] = []
    total_images = len(image_files)
    for index, image_file in enumerate(image_files):
        try:
            result = generator.analyze_image(
                image_file,
                location_hint=location_hint,
                post_context=post_context,
                image_index=index,
                total_images=total_images,
            )
        except Exception as exc:
            warnings.append(f"{Path(image_file).name}: vision metadata failed: {exc}")
            continue

        if not result.get("success"):
            warnings.append(
                f"{Path(image_file).name}: vision metadata failed: {result.get('error', 'unknown error')}"
            )
            continue

        analysis = dict(result.get("analysis") or {})
        analysis["heading"] = post_context.get("title", "") or Path(image_file).stem
        analysis["heading_level"] = 2
        metadata_dict[image_file] = analysis

    if not warnings:
        warnings.append("vision metadata enabled")
    return metadata_dict, warnings


__all__ = [
    "YOMetadataGenerator",
    "build_basic_metadata",
    "build_basic_metadata_map",
    "build_native_metadata_map",
]
