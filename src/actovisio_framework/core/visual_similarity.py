"""Deterministic, dependency-light visual similarity helpers.

Pictovap must not download remote images while planning an article.  This
module therefore computes a compact fingerprint only when an adapter already
has a local image, and also accepts the same serialized fingerprint from
external adapters.  The result is a useful editorial diversity signal without
introducing an ML model or a network dependency.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, cast


_HASH_SIZE = 16
_HASH_BITS = _HASH_SIZE * _HASH_SIZE
_HASH_HEX_WIDTH = (_HASH_BITS + 3) // 4


def compute_visual_fingerprint(path: str | Path, *, size: int = _HASH_SIZE) -> str | None:
    """Return a compact perceptual fingerprint for a local image.

    The fingerprint combines an average grayscale hash with a quantized mean
    RGB color.  It is intentionally not a content identifier and must not be
    used for copyright or identity claims.  Invalid, missing, or unsupported
    files return ``None`` so a provider can still participate normally.
    """
    if size < 4 or size > 32:
        raise ValueError("size must be between 4 and 32")
    try:
        from PIL import Image

        with Image.open(Path(path)) as image:
            rgb = image.convert("RGB")
            sample = rgb.resize((size, size), Image.Resampling.LANCZOS)
            flattened_data = getattr(sample, "get_flattened_data", None)
            data = flattened_data() if callable(flattened_data) else sample.getdata()
            pixels = list(cast(Iterable[tuple[int, int, int]], data))
            if not pixels:
                return None
            grayscale = [round((r * 299 + g * 587 + b * 114) / 1000) for r, g, b in pixels]
            mean = sum(grayscale) / len(grayscale)
            bits = "".join("1" if value >= mean else "0" for value in grayscale)
            average_hash = f"{int(bits, 2):0{(size * size + 3) // 4}x}"
            mean_rgb = tuple(sum(pixel[index] for pixel in pixels) // len(pixels) for index in range(3))
            color = "".join(f"{value:02x}" for value in mean_rgb)
            return f"ah{size}:{average_hash}:c{color}"
    except (OSError, ValueError, TypeError):
        return None


def _parse_fingerprint(value: Any) -> tuple[int, str, str] | None:
    if not isinstance(value, str):
        return None
    parts = value.split(":")
    if len(parts) != 3 or not parts[0].startswith("ah") or not parts[2].startswith("c"):
        return None
    try:
        size = int(parts[0][2:])
        hash_hex = parts[1]
        color = parts[2][1:]
        if size < 4 or size > 32 or len(hash_hex) != (size * size + 3) // 4 or len(color) != 6:
            return None
        int(hash_hex, 16)
        int(color, 16)
    except (TypeError, ValueError):
        return None
    return size, hash_hex, color


def visual_similarity(left: Any, right: Any) -> float:
    """Return a deterministic similarity ratio in the inclusive range 0..1."""
    parsed_left = _parse_fingerprint(left)
    parsed_right = _parse_fingerprint(right)
    if parsed_left is None or parsed_right is None or parsed_left[0] != parsed_right[0]:
        return 0.0

    _, left_hash, left_color = parsed_left
    _, right_hash, right_color = parsed_right
    left_bits = bin(int(left_hash, 16))[2:].zfill(len(left_hash) * 4)
    right_bits = bin(int(right_hash, 16))[2:].zfill(len(right_hash) * 4)
    hash_similarity = 1.0 - sum(a != b for a, b in zip(left_bits, right_bits)) / len(left_bits)
    left_rgb = [int(left_color[index:index + 2], 16) for index in range(0, 6, 2)]
    right_rgb = [int(right_color[index:index + 2], 16) for index in range(0, 6, 2)]
    color_similarity = 1.0 - sum(abs(a - b) for a, b in zip(left_rgb, right_rgb)) / (255 * 3)
    return round(max(0.0, min(1.0, (hash_similarity * 0.8) + (color_similarity * 0.2))), 4)


def collect_candidate_fingerprints(candidates: list[dict[str, Any]]) -> dict[str, str]:
    """Collect provider fingerprints and compute missing local fingerprints."""
    fingerprints: dict[str, str] = {}
    for candidate in candidates:
        candidate_id = candidate.get("id")
        if not isinstance(candidate_id, str):
            continue
        supplied = candidate.get("visual_fingerprint")
        if isinstance(supplied, str) and _parse_fingerprint(supplied) is not None:
            fingerprints[candidate_id] = supplied
            continue
        local_path = candidate.get("local_path")
        if local_path:
            fingerprint = compute_visual_fingerprint(local_path)
            if fingerprint is not None:
                fingerprints[candidate_id] = fingerprint
    return fingerprints


__all__ = ["collect_candidate_fingerprints", "compute_visual_fingerprint", "visual_similarity"]
