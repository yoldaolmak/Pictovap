"""Metadata generation — vision chain ile."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.core.metadata_generator import build_basic_metadata
from src.pictova.engine.vision_chain import analyze_image_vision_chain, has_any_vision_source


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


def build_native_metadata_map(
    image_files: List[str],
    *,
    location_hint: str = "",
    post_context: Dict[str, Any] | None = None,
    mode: str = "auto",
) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """Vision chain ile metadata üret.

    Öncelik zinciri (vision_chain.py):
      1. Gemini Flash (GEMINI_API_KEY)
      2. Codex CLI web login
      3. Claude CLI web login
    Basic fallback YOK — hiçbiri çalışmıyorsa RuntimeError.
    """
    post_context = post_context or {}
    metadata_dict = build_basic_metadata_map(
        image_files,
        location_hint=location_hint,
        post_context=post_context,
    )

    normalized_mode = str(mode or "auto").strip().lower()
    if normalized_mode == "basic":
        raise RuntimeError(
            "mode=basic reddedildi: Pictova basic fallback kullanmaz. "
            "GEMINI_API_KEY ekle veya codex/claude oturumu aç."
        )

    if normalized_mode not in {"auto", "vision"}:
        raise RuntimeError(f"Bilinmeyen metadata modu: {normalized_mode!r}")

    if not has_any_vision_source():
        raise RuntimeError(
            "Hiç vision kaynağı bulunamadı.\n"
            "Seçenekler:\n"
            "  1. GEMINI_API_KEY=... (.env'e ekle — Google AI Studio, ücretsiz)\n"
            "  2. codex login  (terminalde)\n"
            "  3. claude oturumu (zaten açık ise çalışır)"
        )

    warnings: List[str] = []
    for image_file in image_files:
        try:
            analysis = analyze_image_vision_chain(
                image_file,
                location_hint=location_hint,
                post_context=post_context,
            )
            source = analysis.pop("source", "vision_chain")
            analysis["heading"] = post_context.get("title", "") or Path(image_file).stem
            analysis["heading_level"] = 2
            metadata_dict[image_file] = analysis
            warnings.append(f"{Path(image_file).name}: OK ({source})")
        except RuntimeError as exc:
            raise RuntimeError(
                f"Görsel analizi başarısız: {Path(image_file).name}\n{exc}"
            ) from exc

    return metadata_dict, warnings


__all__ = [
    "build_basic_metadata",
    "build_basic_metadata_map",
    "build_native_metadata_map",
]
