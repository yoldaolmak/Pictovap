#!/usr/bin/env python3
import argparse
from pathlib import Path
import re

from PIL import Image, ImageOps

try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE_LANCZOS = Image.LANCZOS


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = (
        value.replace("ı", "i")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ş", "s")
        .replace("ö", "o")
        .replace("ç", "c")
    )
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-{2,}", "-", value).strip("-")


def build_name(product: str, form_name: str, animal: str, weight: str) -> str:
    parts = [slugify(product), slugify(form_name), slugify(animal)]
    if weight:
        parts.append(slugify(weight))
    return "-".join(part for part in parts if part) + ".jpg"


def crop_to_subject(img: Image.Image, white_threshold: int = 245) -> Image.Image:
    rgb = img.convert("RGB")
    pixels = rgb.load()
    width, height = rgb.size

    min_x, min_y = width, height
    max_x, max_y = -1, -1

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            if r < white_threshold or g < white_threshold or b < white_threshold:
                if x < min_x:
                    min_x = x
                if y < min_y:
                    min_y = y
                if x > max_x:
                    max_x = x
                if y > max_y:
                    max_y = y
            elif r > 250 and g > 250 and b > 250:
                pixels[x, y] = (255, 255, 255)

    if max_x == -1:
        return rgb

    return rgb.crop((min_x, min_y, max_x + 1, max_y + 1))


def export_square(input_path: Path, output_path: Path, size: int, margin_ratio: float) -> None:
    img = ImageOps.exif_transpose(Image.open(input_path)).convert("RGB")
    img = crop_to_subject(img)
    canvas = Image.new("RGB", (size, size), (255, 255, 255))

    max_inner = int(size * (1 - (2 * margin_ratio)))
    scale = min(max_inner / img.width, max_inner / img.height)
    resized = img.resize(
        (max(1, int(img.width * scale)), max(1, int(img.height * scale))),
        RESAMPLE_LANCZOS,
    )

    x = (size - resized.width) // 2
    y = (size - resized.height) // 2
    canvas.paste(resized, (x, y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, "JPEG", quality=95, subsampling=0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output-name", default="")
    parser.add_argument("--product", required=True)
    parser.add_argument("--form", required=True)
    parser.add_argument("--animal", required=True)
    parser.add_argument("--weight", default="")
    parser.add_argument("--size", type=int, default=800)
    parser.add_argument("--margin-ratio", type=float, default=0.06)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_name = args.output_name or build_name(args.product, args.form, args.animal, args.weight)
    output_path = output_dir / output_name

    export_square(input_path, output_path, args.size, args.margin_ratio)
    print(str(output_path))


if __name__ == "__main__":
    main()
