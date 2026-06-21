"""Image processing exports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from src.core.processor import YOImageProcessor, get_vil_images


def process_selected_images(
    image_files: List[str],
    *,
    work_dir: str | None = None,
    auto_saturation: bool = True,
) -> Dict[str, Any]:
    processor = YOImageProcessor(work_dir=Path(work_dir) if work_dir else None)
    processed_images: List[str] = []
    processed_details: Dict[str, Dict[str, Any]] = {}
    panoramic_images: Dict[str, Dict[str, Any]] = {}

    for src_file in image_files:
        dest_file = processor.work_dir / (Path(src_file).stem + "_yo.webp")
        result_data = processor.process_image(
            input_path=src_file,
            output_path=str(dest_file),
            auto_saturation=auto_saturation,
        )
        if result_data.get("is_panoramic"):
            panoramic_images[src_file] = {
                "output": str(dest_file),
                "aspect_ratio": result_data.get("aspect_ratio"),
            }
            continue
        processed_images.append(str(dest_file))
        processed_details[str(dest_file)] = result_data

    return {
        "work_dir": str(processor.work_dir),
        "processed_images": processed_images,
        "processed_details": processed_details,
        "panoramic_images": panoramic_images,
    }


__all__ = ["YOImageProcessor", "get_vil_images", "process_selected_images"]
