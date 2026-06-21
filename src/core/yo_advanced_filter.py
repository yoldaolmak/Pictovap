#!/usr/bin/env python3
"""
YO OS Advanced Cinematic Filter
Professional color grading with gradient overlay (no white blown-out)
"""

from PIL import Image, ImageEnhance, ImageDraw, ImageFilter
from pathlib import Path
import numpy as np


class YOAdvancedFilter:
    """Cinematic Blue/Teal filter with soft overlay blending"""

    @staticmethod
    def apply_cinematic_grade(img: Image.Image) -> Image.Image:
        """Apply professional cinematic color grade

        Pipeline:
        1. Curves: Lift blacks slightly, crush whites slightly
        2. Color: Blue teal shadows, warm highlights
        3. Soft light overlay (professional blend)
        4. Saturation + contrast
        """
        # Ensure RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Convert to numpy for advanced operations
        img_array = np.array(img, dtype=np.float32) / 255.0

        # ===== 1. CURVES (Cinematic S-curve) =====
        # Lift blacks, crush whites slightly for film look
        r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]

        # Aggressive S-curve: blacks +8%, mids neutral, whites -5%
        r = np.power(r, 0.92) * 1.10  # Lift blacks more
        g = np.power(g, 0.92) * 1.10
        b = np.power(b, 0.92) * 1.10

        r = np.where(r > 0.5, r - 0.05, r)  # Crush highlights more
        g = np.where(g > 0.5, g - 0.05, g)
        b = np.where(b > 0.5, b - 0.05, b)

        img_array[:,:,0], img_array[:,:,1], img_array[:,:,2] = r, g, b

        # ===== 2. COLOR GRADE: Blue Teal Shadows (AGGRESSIVE) =====
        # Shadows: +blue, -red
        # Highlights: +warm, neutral
        for i in range(3):
            if i == 0:  # Red channel
                img_array[:,:,i] = img_array[:,:,i] * 0.95  # Shadows: -red (more)
                img_array[:,:,i] = np.where(img_array[:,:,i] > 0.6,
                                            img_array[:,:,i] * 1.05, img_array[:,:,i])
            elif i == 2:  # Blue channel
                img_array[:,:,i] = img_array[:,:,i] * 1.20  # Shadows: +blue (aggressive)

        # ===== 3. SOFT LIGHT OVERLAY (Cinematic gradient) =====
        # Create teal gradient overlay (top-left to bottom-right)
        h, w = img_array.shape[:2]
        gradient = np.zeros((h, w, 3), dtype=np.float32)

        # Teal color (#1a4d5c normalized)
        teal = np.array([0.1, 0.3, 0.36])

        for y in range(h):
            for x in range(w):
                # Diagonal gradient strength (0.1 at corners, 0.2 at center)
                strength = 0.08 + (0.1 * ((x/w + y/h) / 2))
                gradient[y, x] = teal * strength

        # Soft Light blend: (img < 0.5) ? (2*img*overlay) : (1 - 2*(1-img)*(1-overlay))
        blend = np.where(
            img_array < 0.5,
            2 * img_array * (img_array + gradient),
            1 - 2 * (1 - img_array) * (1 - img_array - gradient)
        )

        # Blend strength: 28% overlay (aggressive)
        img_array = img_array * 0.72 + blend * 0.28

        # ===== 4. SATURATION + CONTRAST (AGGRESSIVE) =====
        # Convert back to PIL, apply with ImageEnhance
        img_blend = Image.fromarray((np.clip(img_array, 0, 1) * 255).astype(np.uint8))

        # Saturation: +14%
        img_blend = ImageEnhance.Color(img_blend).enhance(1.14)

        # Contrast: +15%
        img_blend = ImageEnhance.Contrast(img_blend).enhance(1.15)

        # Brightness: +4% (airy but not blown)
        img_blend = ImageEnhance.Brightness(img_blend).enhance(1.04)

        # Sharpness: +1.2x
        img_blend = img_blend.filter(ImageFilter.UnsharpMask(radius=1.2, percent=12, threshold=2))

        return img_blend


def test_advanced_filter():
    """Test advanced filter on kalenderis.jpg"""
    test_image = Path.home() / "Downloads" / "kalenderis.jpg"

    if not test_image.exists():
        print(f"✗ Test image not found: {test_image}")
        return

    print("🎬 ADVANCED CINEMATIC FILTER TEST\n")
    print("=" * 60)

    # Load & resize
    img = Image.open(test_image)
    print(f"📷 Original: {img.width}x{img.height}")

    # Final size: 1200px width
    target_w = 1200
    target_h = int(target_w * img.height / img.width)
    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    print(f"🖼️  Final: {img.width}x{img.height}")

    # Apply filter
    print("\n✨ APPLYING ADVANCED CINEMATIC FILTER:")
    print("  ✓ Cinematic S-curve (blacks lifted, whites crushed)")
    print("  ✓ Blue/Teal color grade (shadows)")
    print("  ✓ Soft Light overlay (15% strength)")
    print("  ✓ Saturation +6%")
    print("  ✓ Contrast +8%")
    print("  ✓ Brightness +2% (no blown-out)")
    print("  ✓ Sharpness +1.2x")

    img_filtered = YOAdvancedFilter.apply_cinematic_grade(img)

    # Save
    output = Path.home() / "Downloads" / "kalenderis_ADVANCED_FILTER.webp"
    img_filtered.save(output, 'WEBP', quality=85, method=6)
    size_kb = output.stat().st_size / 1024

    print(f"\n💾 SAVED: {output.name} ({size_kb:.1f}KB)")
    print("=" * 60)
    print("✅ Karşılaştır:")
    print(f"   Orijinal: ~/Downloads/kalenderis.jpg")
    print(f"   Filtreli: {output}")
    print("=" * 60)


if __name__ == "__main__":
    test_advanced_filter()
