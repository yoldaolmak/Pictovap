#!/usr/bin/env python3
"""YO OS adaptive cinematic filter."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageEnhance


class YOAdaptiveFilter:
    """Adaptive cinematic filter that analyzes and adjusts to image content."""

    TARGET_BRIGHTNESS = 0.50
    TARGET_SATURATION = 0.34
    TARGET_CONTRAST = 0.17
    TARGET_COLOR_TEMP = 0.0
    SIGNATURE_VIGNETTE = 0.08
    SIGNATURE_MATTE_LIFT = 0.035
    SIGNATURE_WARM_HIGHLIGHTS = np.array([1.015, 1.005, 0.985], dtype=np.float32)
    SIGNATURE_COOL_SHADOWS = np.array([0.985, 0.995, 1.03], dtype=np.float32)

    def __init__(self):
        self.params = {}

    def _measure_stats(self, img: Image.Image) -> dict:
        arr = np.array(img, dtype=np.float32) / 255.0
        r = arr[:, :, 0]
        g = arr[:, :, 1]
        b = arr[:, :, 2]
        brightness = float(np.mean(arr))
        mx = np.maximum(np.maximum(r, g), b)
        mn = np.minimum(np.minimum(r, g), b)
        saturation = float(np.mean((mx - mn) / (mx + 1e-6)))
        contrast = float(np.std(arr))
        color_temp = float(np.mean(b) - np.mean(r))
        return {
            "brightness": brightness,
            "saturation": saturation,
            "contrast": contrast,
            "color_temp": color_temp,
        }

    def _normalize_house_style(self, img: Image.Image) -> tuple[Image.Image, dict]:
        stats_before = self._measure_stats(img)
        brightness_factor = float(
            np.clip(self.TARGET_BRIGHTNESS / max(stats_before["brightness"], 0.01), 0.92, 1.10)
        )
        saturation_factor = float(
            np.clip(self.TARGET_SATURATION / max(stats_before["saturation"], 0.05), 0.90, 1.12)
        )
        contrast_factor = float(
            np.clip(self.TARGET_CONTRAST / max(stats_before["contrast"], 0.08), 0.82, 1.10)
        )
        img = ImageEnhance.Brightness(img).enhance(brightness_factor)
        img = ImageEnhance.Color(img).enhance(saturation_factor)
        img = ImageEnhance.Contrast(img).enhance(contrast_factor)
        stats_after = self._measure_stats(img)
        temp_delta = self.TARGET_COLOR_TEMP - stats_after["color_temp"]
        if abs(temp_delta) > 0.01:
            arr = np.array(img, dtype=np.float32) / 255.0
            red_scale = float(np.clip(1.0 - temp_delta * 0.35, 0.97, 1.03))
            blue_scale = float(np.clip(1.0 + temp_delta * 0.35, 0.97, 1.03))
            arr[:, :, 0] *= red_scale
            arr[:, :, 2] *= blue_scale
            arr = np.clip(arr, 0, 1)
            img = Image.fromarray((arr * 255).astype(np.uint8))
            stats_after = self._measure_stats(img)
        return img, {
            "before": stats_before,
            "after": stats_after,
            "brightness_factor": brightness_factor,
            "saturation_factor": saturation_factor,
            "contrast_factor": contrast_factor,
        }

    def _apply_signature_grade(self, img: Image.Image) -> tuple[Image.Image, dict]:
        arr = np.array(img, dtype=np.float32) / 255.0
        h, w = arr.shape[:2]
        luma = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        shadows = np.clip((0.48 - luma) / 0.48, 0.0, 1.0)[..., None]
        highlights = np.clip((luma - 0.52) / 0.48, 0.0, 1.0)[..., None]
        arr = arr * (1.0 + shadows * (self.SIGNATURE_COOL_SHADOWS - 1.0))
        arr = arr * (1.0 + highlights * (self.SIGNATURE_WARM_HIGHLIGHTS - 1.0))
        arr = arr * (1.0 - self.SIGNATURE_MATTE_LIFT) + self.SIGNATURE_MATTE_LIFT

        yy, xx = np.mgrid[0:h, 0:w]
        nx = (xx / max(w - 1, 1)) * 2.0 - 1.0
        ny = (yy / max(h - 1, 1)) * 2.0 - 1.0
        radius = np.sqrt(nx * nx + ny * ny)
        vignette = 1.0 - np.clip((radius - 0.15) / 1.1, 0.0, 1.0) * self.SIGNATURE_VIGNETTE
        arr *= vignette[..., None]

        arr = np.clip(arr, 0, 1)
        return Image.fromarray((arr * 255).astype(np.uint8)), {
            "vignette": self.SIGNATURE_VIGNETTE,
            "matte_lift": self.SIGNATURE_MATTE_LIFT,
            "warm_highlights": self.SIGNATURE_WARM_HIGHLIGHTS.tolist(),
            "cool_shadows": self.SIGNATURE_COOL_SHADOWS.tolist(),
        }

    def apply_cinematic_grade(self, img: Image.Image) -> Image.Image:
        img = img.convert("RGB")
        img, normalize_params = self._normalize_house_style(img)
        img, signature_params = self._apply_signature_grade(img)
        self.params = {**normalize_params, **signature_params}
        return img
