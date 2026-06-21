#!/usr/bin/env python3
"""Yoldaolmak-specific image grade."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageEnhance


class YOYoldaOlmakFilter:
    """Balanced travel grade for yoldaolmak."""

    def __init__(self) -> None:
        self.low_sat_threshold = 0.20
        self.high_sat_threshold = 0.46
        self.vignette_strength = 0.055
        self.bottom_shadow_strength = 0.14
        self.shadow_teal = np.array([18, 63, 63], dtype=np.float32) / 255.0
        self.highlight_terra = np.array([196, 98, 45], dtype=np.float32) / 255.0

    def analyze_image(self, img: Image.Image) -> dict:
        arr = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
        luminance = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        maxc = arr.max(axis=2)
        minc = arr.min(axis=2)
        saturation = np.divide(maxc - minc, maxc, out=np.zeros_like(maxc), where=maxc != 0)
        return {
            "brightness": float(luminance.mean()),
            "saturation": float(saturation.mean()),
            "contrast": float(luminance.std()),
        }

    def apply_filter(self, img: Image.Image) -> Image.Image:
        img = img.convert("RGB")
        stats = self.analyze_image(img)

        brightness = stats["brightness"]
        if brightness < 0.42:
            brightness_factor = min(1.10, 1.0 + (0.46 - brightness) * 0.30)
        elif brightness > 0.62:
            brightness_factor = max(0.94, 1.0 - (brightness - 0.56) * 0.22)
        else:
            brightness_factor = 1.0
        img = ImageEnhance.Brightness(img).enhance(brightness_factor)

        saturation = stats["saturation"]
        if saturation > self.high_sat_threshold:
            saturation_factor = 0.90
        elif saturation < self.low_sat_threshold:
            saturation_factor = 1.16
        else:
            saturation_factor = 1.03
        img = ImageEnhance.Color(img).enhance(saturation_factor)

        contrast_factor = 1.04 if stats["contrast"] > 0.18 else 1.08
        img = ImageEnhance.Contrast(img).enhance(contrast_factor)

        arr = np.asarray(img, dtype=np.float32) / 255.0
        h, w = arr.shape[:2]
        luminance = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2])[:, :, None]

        shadow_mask = np.clip((0.52 - luminance) / 0.52, 0, 1) * 0.045
        highlight_mask = np.clip((luminance - 0.50) / 0.50, 0, 1) * 0.025
        arr = arr * (1 - shadow_mask) + self.shadow_teal * shadow_mask
        arr = arr * (1 - highlight_mask) + self.highlight_terra * highlight_mask

        y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
        bottom = np.clip((y - 0.68) / 0.32, 0, 1) ** 1.35
        arr *= 1 - (bottom * self.bottom_shadow_strength)

        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        cx, cy = w * 0.5, h * 0.45
        distance = np.sqrt(((xx - cx) / (w * 0.74)) ** 2 + ((yy - cy) / (h * 0.74)) ** 2)
        vignette = np.clip((distance - 0.55) / 0.55, 0, 1)[:, :, None]
        arr *= 1 - (vignette * self.vignette_strength)

        arr = np.clip(arr, 0, 1)
        return Image.fromarray((arr * 255).astype(np.uint8), "RGB")
