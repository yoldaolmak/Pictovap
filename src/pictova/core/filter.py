#!/usr/bin/env python3
"""
YO OS Adaptive Cinematic Filter
Intelligent color grading that adjusts to each image's characteristics.

Core logic: color temperature (b_mean - r_mean) drives the grading decisions.
  - Warm image (r > b): needs cooling → more teal overlay, stronger blue boost
  - Cold image (b > r): already cool → less overlay, minimal blue boost
  - Neutral: standard cinematic parameters
"""

from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path
import numpy as np


class YOAdaptiveFilter:
    """Adaptive cinematic filter that analyzes and adjusts to image content"""

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

        # Signature split-tone: cooler shadows, slightly warm highlights.
        arr = arr * (1.0 + shadows * (self.SIGNATURE_COOL_SHADOWS - 1.0))
        arr = arr * (1.0 + highlights * (self.SIGNATURE_WARM_HIGHLIGHTS - 1.0))

        # Matte lift keeps blacks soft and recognizable across the set.
        arr = arr * (1.0 - self.SIGNATURE_MATTE_LIFT) + self.SIGNATURE_MATTE_LIFT

        # Very light vignette for a final editorial finish.
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

    def analyze_image(self, img_array: np.ndarray) -> dict:
        """Analyze image characteristics and compute optimal filter parameters.

        Decision hierarchy:
          1. Aspect ratio → panoramic detection
          2. Brightness → exposure compensation
          3. Saturation → color richness adjustment
          4. Contrast (std_dev) → tonal range adjustment
          5. Highlights / shadows ratio → curve endpoint control
          6. Color temperature (b - r) → drives blue_boost, red_reduction, overlay

        Args:
            img_array: normalized float32 array (0-1), shape (H, W, 3)

        Returns:
            dict with all computed parameters
        """
        h, w = img_array.shape[:2]
        r = img_array[:, :, 0]
        g = img_array[:, :, 1]
        b = img_array[:, :, 2]

        # ── ASPECT RATIO ─────────────────────────────────────────────────────
        aspect_ratio = w / h
        is_panoramic = aspect_ratio > 2.0

        # ── BRIGHTNESS ───────────────────────────────────────────────────────
        # Mean luminance across all channels.
        brightness = float(np.mean(img_array))

        brightness_factor = 1.0
        if brightness < 0.25:
            brightness_factor = 1.15   # very dark → lift
        elif brightness < 0.35:
            brightness_factor = 1.08   # dark → mild lift
        elif brightness > 0.75:
            brightness_factor = 0.85   # very bright → pull down
        elif brightness > 0.65:
            brightness_factor = 0.92   # bright → mild pull

        # ── SATURATION ───────────────────────────────────────────────────────
        # HSV saturation approximation: (max - min) / max
        max_val = np.maximum(np.maximum(r, g), b)
        min_val = np.minimum(np.minimum(r, g), b)
        saturation_map = (max_val - min_val) / (max_val + 1e-6)
        avg_saturation = float(np.mean(saturation_map))

        saturation_factor = 1.05   # default: mild boost
        if avg_saturation > 0.50:
            saturation_factor = 0.94   # oversaturated → reduce
        elif avg_saturation > 0.45:
            saturation_factor = 0.99
        elif avg_saturation < 0.20:
            saturation_factor = 1.12   # very dull → strong boost
        elif avg_saturation < 0.28:
            saturation_factor = 1.08

        # ── CONTRAST ─────────────────────────────────────────────────────────
        std_dev = float(np.std(img_array))

        contrast_factor = 1.08   # default
        if std_dev < 0.10:
            contrast_factor = 1.20   # very flat → strong boost
        elif std_dev < 0.13:
            contrast_factor = 1.14
        elif std_dev > 0.20:
            contrast_factor = 1.06   # already contrasty → gentle

        # ── HIGHLIGHTS ───────────────────────────────────────────────────────
        luma = 0.299 * r + 0.587 * g + 0.114 * b
        bright_ratio = float(np.mean(luma > 0.92))

        whites_crush = 0.05
        if bright_ratio > 0.15:
            whites_crush = 0.02   # many bright pixels → preserve
        elif bright_ratio < 0.05:
            whites_crush = 0.07   # few blown pixels → safe to crush

        # ── SHADOWS ──────────────────────────────────────────────────────────
        dark_ratio = float(np.mean(luma < 0.12))

        blacks_lift = 1.05
        if dark_ratio > 0.25:
            blacks_lift = 1.08   # very dark image → lift more
        elif dark_ratio < 0.08:
            blacks_lift = 1.02   # mostly bright → subtle lift

        # ── COLOR TEMPERATURE ────────────────────────────────────────────────
        # color_temp > 0  →  image is COOL (blue-dominant)
        # color_temp < 0  →  image is WARM (red-dominant)
        r_mean = float(np.mean(r))
        b_mean = float(np.mean(b))
        color_temp = b_mean - r_mean   # signed: cool=positive, warm=negative

        # blue_boost: warm images need more cooling (teal), cool images get less
        if color_temp > 0.12:
            blue_boost = 1.02    # already very cool → barely touch blue
        elif color_temp > 0.06:
            blue_boost = 1.05    # cool → mild boost
        elif color_temp > -0.04:
            blue_boost = 1.09    # neutral → standard cinematic boost
        elif color_temp > -0.10:
            blue_boost = 1.13    # warm → cool it down
        else:
            blue_boost = 1.16    # very warm → strong cooling

        # red_reduction: warm images carry excess red; cool images keep their red
        if color_temp < -0.10:
            red_reduction = 0.95   # very warm → reduce red more
        elif color_temp < -0.04:
            red_reduction = 0.97
        elif color_temp < 0.06:
            red_reduction = 0.99   # neutral → standard
        else:
            red_reduction = 1.00   # cool → nearly no red reduction

        # overlay_strength: teal overlay benefits warm/neutral images most.
        # For cool images it adds to existing blue → keep low.
        # Base: lower saturation → slightly more overlay (adds colour to dull images)
        base_overlay = 0.10 + 0.06 * (1.0 - avg_saturation)   # 0.10–0.16

        # Temperature modifier: warm → raise overlay, cool → lower overlay
        temp_mod = float(np.clip(-color_temp * 0.16, -0.04, 0.04))
        overlay_strength = float(np.clip(base_overlay + temp_mod, 0.08, 0.18))

        # ── SATURATION TARGET ────────────────────────────────────────────────
        # Channel boost + S-curve + overlay adımlarının kombine etkisini
        # formülle modellemek güvenilmez. Bunun yerine:
        # → Hedef saturation'u şimdi hesapla, filtreden sonra o değere normalize et.
        target_saturation = avg_saturation * saturation_factor

        # ── PRINT & RETURN ───────────────────────────────────────────────────
        return {
            # raw measurements
            "brightness":      brightness,
            "avg_saturation":  avg_saturation,
            "std_dev":         std_dev,
            "bright_ratio":    bright_ratio,
            "dark_ratio":      dark_ratio,
            "color_temp":      color_temp,    # signed; positive = cool
            "r_mean":          r_mean,
            "b_mean":          b_mean,
            # image geometry
            "aspect_ratio":    aspect_ratio,
            "is_panoramic":    is_panoramic,
            # adjustment factors
            "brightness_factor":  brightness_factor,
            "saturation_factor":  saturation_factor,
            "contrast_factor":    contrast_factor,
            "whites_crush":       whites_crush,
            "blacks_lift":        blacks_lift,
            "blue_boost":         blue_boost,
            "red_reduction":      red_reduction,
            "overlay_strength":   overlay_strength,
            "target_saturation":  float(target_saturation),
        }

    def apply_cinematic_grade(self, img: Image.Image) -> Image.Image:
        """Apply adaptive cinematic color grade.

        Args:
            img: PIL Image (RGB)

        Returns:
            filtered image
        """
        if img.mode != 'RGB':
            img = img.convert('RGB')

        img_array = np.array(img, dtype=np.float32) / 255.0

        # Analyze image
        self.params = self.analyze_image(img_array)
        p = self.params

        # Diagnostic output
        temp_label = (
            "soğuk"   if p['color_temp'] >  0.06 else
            "sıcak"   if p['color_temp'] < -0.04 else
            "nötr"
        )
        print(f"  📊 Analiz:")
        print(f"     Brightness:   {p['brightness']:.2f}  → {p['brightness_factor']:.2f}x")
        print(f"     Saturation:   {p['avg_saturation']:.2f}  → {p['saturation_factor']:.2f}x")
        print(f"     Contrast:     {p['std_dev']:.3f} → {p['contrast_factor']:.2f}x")
        print(f"     Color temp:   {p['color_temp']:+.3f} ({temp_label})")
        print(f"     Blue boost:   {p['blue_boost']:.2f}x  |  Red reduction: {p['red_reduction']:.2f}x")
        print(f"     Overlay:      {p['overlay_strength']:.1%}")

        if p['is_panoramic']:
            print(f"  ⚠️  PANORAMIK: {p['aspect_ratio']:.2f}:1 (pillar pages için)")

        # ── S-CURVE: blacks lift + whites crush ──────────────────────────────
        r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]

        # Gamma lift on shadows (power < 1 brightens midtones/shadows)
        r = np.power(np.clip(r, 0, 1), 0.92) * p['blacks_lift']
        g = np.power(np.clip(g, 0, 1), 0.92) * p['blacks_lift']
        b = np.power(np.clip(b, 0, 1), 0.92) * p['blacks_lift']

        # Smooth highlight crush: only pixels above 0.5, proportional
        crush = p['whites_crush']
        r = np.where(r > 0.5, r - crush * ((r - 0.5) / 0.5), r)
        g = np.where(g > 0.5, g - crush * ((g - 0.5) / 0.5), g)
        b = np.where(b > 0.5, b - crush * ((b - 0.5) / 0.5), b)

        img_array[:, :, 0] = r
        img_array[:, :, 1] = g
        img_array[:, :, 2] = b

        # ── COLOR GRADE ──────────────────────────────────────────────────────
        # Red: global reduction (shadows-to-highlights)
        img_array[:, :, 0] *= p['red_reduction']

        # Red: slight recovery in highlights (preserve skin/warmth in bright areas)
        img_array[:, :, 0] = np.where(
            img_array[:, :, 0] > 0.6,
            img_array[:, :, 0] * 1.04,
            img_array[:, :, 0]
        )

        # Blue: global boost driven by color temperature
        img_array[:, :, 2] *= p['blue_boost']

        # ── TEAL SOFT-LIGHT OVERLAY ───────────────────────────────────────────
        # Uniform teal layer (no spatial gradient — gradient was semantically arbitrary).
        # Strength varies only with image analysis, not position.
        h_px, w_px = img_array.shape[:2]
        overlay_str = p['overlay_strength']

        teal = np.array([0.10, 0.30, 0.36], dtype=np.float32)    # #1a4d5c normalised

        # Vectorised: broadcast teal over (H, W, 3)
        gradient = np.broadcast_to(teal * overlay_str, (h_px, w_px, 3)).copy()

        # Soft-light blend formula
        blend = np.where(
            img_array < 0.5,
            2.0 * img_array * (img_array + gradient),
            1.0 - 2.0 * (1.0 - img_array) * (1.0 - img_array - gradient)
        )

        img_array = img_array * (1.0 - overlay_str) + blend * overlay_str
        img_array = np.clip(img_array, 0, 1)

        # ── CONTRAST / BRIGHTNESS ─────────────────────────────────────────────
        img_blend = Image.fromarray((img_array * 255).astype(np.uint8))
        img_blend = ImageEnhance.Contrast(img_blend).enhance(p['contrast_factor'])
        img_blend = ImageEnhance.Brightness(img_blend).enhance(p['brightness_factor'])

        # Pull highlights slightly back after the grade to avoid crunchy travel shots.
        arr_post = np.array(img_blend, dtype=np.float32) / 255.0
        highlight_mask = arr_post > 0.82
        arr_post[highlight_mask] = 0.82 + (arr_post[highlight_mask] - 0.82) * 0.75
        img_blend = Image.fromarray((np.clip(arr_post, 0, 1) * 255).astype(np.uint8))

        # ── SATURATION NORMALIZATION (post-filter) ────────────────────────────
        # Filtre adımları (channel boost, S-curve, overlay) saturation'ı değiştirir.
        # Gerçek saturation'ı ölçüp hedef değere normalize et.
        arr_final = np.array(img_blend, dtype=np.float32) / 255.0
        rf, gf, bf = arr_final[:, :, 0], arr_final[:, :, 1], arr_final[:, :, 2]
        mx_f = np.maximum(np.maximum(rf, gf), bf)
        mn_f = np.minimum(np.minimum(rf, gf), bf)
        actual_sat = float(np.mean((mx_f - mn_f) / (mx_f + 1e-6)))

        target_sat = p['target_saturation']
        if actual_sat > 1e-3:
            sat_correction = float(np.clip(target_sat / actual_sat, 0.92, 1.08))
            img_blend = ImageEnhance.Color(img_blend).enhance(sat_correction)
            print(f"     Sat normalize: {actual_sat:.3f} → {target_sat:.3f} ({sat_correction:.2f}x)")

        # ── HOUSE STYLE NORMALIZATION ────────────────────────────────────────
        img_blend, house_style = self._normalize_house_style(img_blend)
        self.params["house_style"] = house_style
        print(
            "     House style:"
            f" b {house_style['before']['brightness']:.3f}->{house_style['after']['brightness']:.3f},"
            f" s {house_style['before']['saturation']:.3f}->{house_style['after']['saturation']:.3f},"
            f" c {house_style['before']['contrast']:.3f}->{house_style['after']['contrast']:.3f}"
        )

        # Final signature pass: subtle split-toning and matte finish.
        img_blend, signature = self._apply_signature_grade(img_blend)
        self.params["signature"] = signature
        print(
            "     Signature:"
            f" matte {signature['matte_lift']:.3f},"
            f" vignette {signature['vignette']:.3f}"
        )

        # ── SHARPNESS ─────────────────────────────────────────────────────────
        img_blend = img_blend.filter(
            ImageFilter.UnsharpMask(radius=1.1, percent=10, threshold=3)
        )

        return img_blend


def process_image(image_path: str, output_path: str = None) -> Path:
    """Process single image with adaptive filter.

    Args:
        image_path: path to image
        output_path: optional output path (default: <stem>_ADAPTIVE.webp)

    Returns:
        output file path
    """
    img_path = Path(image_path)
    if not img_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    img = Image.open(img_path)

    target_w = 1200
    img = img.resize((target_w, int(target_w * img.height / img.width)),
                     Image.Resampling.LANCZOS)

    filter_obj = YOAdaptiveFilter()
    img_filtered = filter_obj.apply_cinematic_grade(img)

    if output_path is None:
        output_path = img_path.parent / f"{img_path.stem}_ADAPTIVE.webp"

    img_filtered.save(output_path, 'WEBP', quality=85, method=6)
    return Path(output_path)


if __name__ == "__main__":
    import sys
    test_image = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads" / "IMG_7271.jpeg"
    if test_image.exists():
        print(f"🎬 YO ADAPTIVE FILTER\n{'='*50}")
        result = process_image(str(test_image))
        print(f"\n✅ {result.name} ({result.stat().st_size / 1024:.1f} KB)")
    else:
        print(f"Image not found: {test_image}")
