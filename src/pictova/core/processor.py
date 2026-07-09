#!/usr/bin/env python3
"""
YO OS Image Processor — Complete pipeline
- Image load, crop, filter, metadata
- Blue/Teal YO filter
- Automatic saturation analysis
- WebP export
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import subprocess
import json
import numpy as np

from pictova.utils.config import get_vil_dir, load_project_env

load_project_env()

class YOImageProcessor:
    """Image processing with YO Blue/Teal filter"""

    # Filter spec
    FILTER_SPEC = {
        "blue_channel_boost": 1.08,
        "contrast": 1.10,
        "saturation": 1.08,
        "brightness": 1.05,
        "sharpness_radius": 1.5,
        "sharpness_percent": 15,
    }

    LANDSCAPE_SIZE = (1200, 750)
    PORTRAIT_SIZE = (900, 1200)
    SQUARE_SIZE = (1200, 1200)

    def __init__(self, work_dir: Path = None):
        self.work_dir = work_dir or Path("/tmp/yo_image_work")
        self.work_dir.mkdir(exist_ok=True)

    def _heic_to_jpeg(self, input_p: Path) -> Path:
        """Convert HEIC/HEIF to JPEG using macOS sips. Returns path to converted file.

        Gereksinim: Terminal'e System Settings > Privacy > Full Disk Access verilmiş olmalı.
        """
        import shutil
        if not shutil.which("sips"):
            raise RuntimeError("sips not found — HEIC conversion requires macOS")
        jpeg_path = self.work_dir / (input_p.stem + "_heic_tmp.jpg")
        result = subprocess.run(
            ["sips", "-s", "format", "jpeg", str(input_p), "--out", str(jpeg_path)],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0 or not jpeg_path.exists():
            stderr = result.stderr.decode()
            if "error 13" in stderr.lower() or "permission" in stderr.lower():
                raise PermissionError(
                    f"HEIC dönüştürme başarısız — Photos Library için Full Disk Access gerekli.\n"
                    f"System Settings > Privacy & Security > Full Disk Access → Terminal'i ekle.\n"
                    f"Dosya: {input_p}"
                )
            raise RuntimeError(f"sips HEIC conversion failed: {stderr}")
        return jpeg_path

    def detect_orientation(self, img: Image.Image) -> str:
        """Detect if image is landscape or portrait"""
        return "landscape" if img.width >= img.height else "portrait"

    def resize_for_processing(self, img: Image.Image, max_width: int = 2000) -> Image.Image:
        """Resize image maintaining aspect ratio

        Args:
            img: PIL Image
            max_width: target width (if image wider, resize down)

        Returns:
            resized image
        """
        if img.width <= max_width:
            return img

        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        resized = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        print(f"  ✓ Resized: {img.width}x{img.height} → {resized.width}x{resized.height}")
        return resized

    def target_size(self, img: Image.Image) -> tuple[int, int]:
        aspect_ratio = img.width / max(img.height, 1)
        if 0.92 <= aspect_ratio <= 1.08:
            return self.SQUARE_SIZE
        if img.height > img.width:
            return self.PORTRAIT_SIZE
        return self.LANDSCAPE_SIZE

    def crop_image(self, img: Image.Image) -> tuple[Image.Image, tuple[int, int]]:
        """Create a consistent editorial crop instead of loose resize."""
        target_size = self.target_size(img)
        centering = self._smart_centering(img, target_size)
        cropped = ImageOps.fit(
            img,
            target_size,
            method=Image.Resampling.LANCZOS,
            centering=centering,
        )
        print(f"  ✓ Cropped: {img.width}x{img.height} → {cropped.width}x{cropped.height}")
        return cropped, target_size

    def _smart_centering(self, img: Image.Image, target_size: tuple[int, int]) -> tuple[float, float]:
        """Bias crop towards the visually densest area instead of dead center."""
        sample = img.convert("L").resize((96, 96), Image.Resampling.BILINEAR)
        arr = np.asarray(sample, dtype=np.float32) / 255.0
        grad_x = np.abs(np.diff(arr, axis=1, prepend=arr[:, :1]))
        grad_y = np.abs(np.diff(arr, axis=0, prepend=arr[:1, :]))
        energy = grad_x + grad_y

        col_energy = energy.sum(axis=0)
        row_energy = energy.sum(axis=1)
        x_idx = float(np.argmax(col_energy)) / max(len(col_energy) - 1, 1)
        y_idx = float(np.argmax(row_energy)) / max(len(row_energy) - 1, 1)

        base_x = 0.5
        base_y = 0.5
        if target_size == self.PORTRAIT_SIZE:
            base_y = 0.38
        elif target_size == self.LANDSCAPE_SIZE:
            base_y = 0.46

        center_x = float(np.clip((base_x * 0.65) + (x_idx * 0.35), 0.25, 0.75))
        center_y = float(np.clip((base_y * 0.7) + (y_idx * 0.3), 0.20, 0.80))
        return center_x, center_y

    def apply_yo_filter(self, img: Image.Image, saturation_mod: float = 0) -> tuple:
        """Apply selected YO image filter profile.

        Args:
            img: PIL Image (RGB)
            saturation_mod: unused (kept for backward compatibility)

        Returns:
            tuple (filtered_image, params_dict)
        """
        profile = os.getenv("YO_IMAGE_FILTER_PROFILE", "adaptive").strip().lower()

        # Import filter from canonical location (src/core/filter.py)
        # Falls back to project-root module for legacy compatibility
        def _load_adaptive() -> "YOAdaptiveFilter":
            try:
                from pictova.core.filter import YOAdaptiveFilter as _F
                return _F()
            except ImportError:
                pass
            import importlib.util, pathlib
            root = pathlib.Path(__file__).resolve().parents[2]  # project root
            spec = importlib.util.spec_from_file_location("yo_adaptive_filter", root / "yo_adaptive_filter.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.YOAdaptiveFilter()

        if profile in {"yoldaolmak", "yo-yoldaolmak"}:
            try:
                from pictova.core.filter import YOAdaptiveFilter
                filter_obj = YOAdaptiveFilter()
            except ImportError:
                filter_obj = _load_adaptive()
            img_filtered = filter_obj.apply_cinematic_grade(img)
            print("  ✓ YO Filter applied (yoldaolmak profile → adaptive)")
            return img_filtered, filter_obj.params

        filter_obj = _load_adaptive()
        img_filtered = filter_obj.apply_cinematic_grade(img)
        print("  ✓ YO Adaptive Filter applied")
        return img_filtered, filter_obj.params

    def analyze_saturation_need(self, img: Image.Image) -> float:
        """Analyze if image needs saturation boost or reduction

        Returns:
            float: saturation modification (-0.15 to +0.15)
        """
        # Convert to HSV for saturation analysis
        from PIL import ImageStat

        # Simple heuristic: if image is already very saturated, reduce
        # if dull, boost

        # Count distinct colors (rough colorfulness metric)
        stat = ImageStat.Stat(img)
        std_dev = sum(stat.stddev) / 3  # avg std dev across channels

        # Heuristic: high std_dev = already saturated
        if std_dev > 80:
            mod = -0.08  # reduce saturation
            reason = "already saturated"
        elif std_dev < 30:
            mod = +0.12  # boost saturation
            reason = "dull image"
        else:
            mod = 0  # keep as is
            reason = "balanced"

        print(f"  ℹ Saturation analysis: {reason} (std_dev={std_dev:.1f})")
        return mod

    def process_image(
        self,
        input_path: str,
        output_path: str,
        auto_saturation: bool = True,
        webp_mode: str = "lossy",
        preserve_exif: bool = False,
    ) -> Dict:
        """Full image processing pipeline

        Args:
            input_path: source file
            output_path: destination WebP
            auto_saturation: auto-detect saturation adjustment

        Returns:
            dict with processing metadata
        """
        input_p = Path(input_path)
        output_p = Path(output_path)

        if not input_p.exists():
            raise FileNotFoundError(f"Image not found: {input_path}")

        print(f"\n📷 Processing: {input_p.name}")

        # HEIC/HEIF → JPEG via sips (macOS) before PIL opens it
        if input_p.suffix.lower() in {".heic", ".heif"}:
            input_p = self._heic_to_jpeg(input_p)
            print(f"  ✓ HEIC converted via sips")

        # Load
        # Normalize EXIF orientation first so rotated phone images are upright.
        img = ImageOps.exif_transpose(Image.open(str(input_p))).convert("RGB")
        orig_size = (img.width, img.height)
        print(f"  Original: {img.width}x{img.height}")

        # Resize if too large (preprocessing for API, efficiency)
        # This step reduces payload size for Cloud Vision API
        if img.width > 3000:
            img = self.resize_for_processing(img, max_width=2500)
            print(f"  ✓ Pre-processed for API")

        img, target_size = self.crop_image(img)

        # Saturation analysis
        sat_mod = 0
        if auto_saturation:
            sat_mod = self.analyze_saturation_need(img)

        # Apply filter
        img, filter_params = self.apply_yo_filter(img, saturation_mod=sat_mod)

        # Clean EXIF unless preserve_exif is True
        if not preserve_exif:
            data = list(img.getdata())
            image_without_exif = Image.new(img.mode, img.size)
            image_without_exif.putdata(data)
            img = image_without_exif
            print(f"  ✓ EXIF cleaned")
        else:
            print(f"  ✓ EXIF preserved")

        # Export WebP
        output_p.parent.mkdir(parents=True, exist_ok=True)
        if webp_mode.lower() == "lossless":
            img.save(str(output_p), 'WEBP', quality=100, method=6, lossless=True)
            print("  ✓ WebP saved (lossless)")
        else:
            img.save(str(output_p), 'WEBP', quality=80, method=6)
            print("  ✓ WebP saved (lossy)")
            
        file_size_kb = output_p.stat().st_size / 1024
        print(f"  ✓ File size: {file_size_kb:.1f} KB")

        arr = np.array(img, dtype=np.float32) / 255.0
        brightness = float(np.mean(arr))
        rgb_max = np.maximum.reduce([arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]])
        rgb_min = np.minimum.reduce([arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]])
        saturation = float(np.mean((rgb_max - rgb_min) / (rgb_max + 1e-6)))

        # Blur analysis
        edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
        blur_score = float(np.var(np.array(edges)))
        print(f"  ✓ Blur score: {blur_score:.1f}")

        return {
            "input": str(input_path),
            "output": str(output_p),
            "original_size": orig_size,
            "final_size": (img.width, img.height),
            "target_size": target_size,
            "saturation_mod": sat_mod,
            "file_size_kb": file_size_kb,
            "brightness": brightness,
            "saturation": saturation,
            "contrast": float(np.std(arr)),
            "blur_score": blur_score,
            "color_temp": float(np.mean(arr[:, :, 2]) - np.mean(arr[:, :, 0])),
            "house_style": filter_params.get("house_style", {}),
            "is_panoramic": filter_params.get("is_panoramic", False),
            "aspect_ratio": filter_params.get("aspect_ratio", 0),
        }


VIL_DIR = get_vil_dir()
ORIGINAL_EXTS = ['jpg', 'jpeg', 'png', 'JPG', 'JPEG', 'PNG']


def get_vil_images(count: int = None, name: str = None) -> List[str]:
    """Get images from ~/Downloads/VIL/

    Args:
        count: number of most recent images (None = all)
        name: partial filename match (case-insensitive)

    Returns:
        list of file paths, sorted by mtime (newest first)
    """
    if not VIL_DIR.exists():
        raise FileNotFoundError(f"VIL klasörü bulunamadı: {VIL_DIR}")

    # Sadece orijinal resimler (webp çıktıları hariç)
    images = []
    for ext in ORIGINAL_EXTS:
        images.extend(VIL_DIR.glob(f"*.{ext}"))

    images = sorted(set(images), key=lambda p: p.stat().st_mtime, reverse=True)

    # İsim filtresi
    if name:
        name_lower = name.lower()
        images = [img for img in images if name_lower in img.stem.lower()]
        if not images:
            raise FileNotFoundError(f"'{name}' ile eşleşen resim bulunamadı")

    # Sayı sınırı
    if count:
        images = images[:count]

    print(f"\n📁 VIL: {len(images)} resim")
    for i, img in enumerate(images, 1):
        print(f"  {i}. {img.name}")

    return [str(img) for img in images]


def process_downloads_images(count: int = 5) -> List[str]:
    """Backward compat — VIL klasörüne yönlendirir"""
    return get_vil_images(count=count)


if __name__ == "__main__":
    processor = YOImageProcessor()

    # Test
    images = process_downloads_images(count=3)
    for src in images[:1]:  # test just first
        dest = Path(src).parent / (Path(src).stem + "_processed.webp")
        result = processor.process_image(src, str(dest))
        print(f"\n✅ Result: {json.dumps(result, indent=2)}")
