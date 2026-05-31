#!/usr/bin/env python3
"""
YO OS — Google Cloud Vision API client for metadata generation
"""

import requests
import base64
from pathlib import Path
from typing import Dict, Optional
import os
from PIL import Image
import io

from settings import load_project_env
from vision_budget import check_budget, consume_budget

load_project_env()


class YOCloudVisionClient:
    """Google Cloud Vision API wrapper for image analysis"""

    MONTHLY_FREE_UNITS = 1000
    WARNING_THRESHOLD = 0.80
    DEFAULT_DAILY_LIMIT = 8

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GOOGLE_CLOUD_VISION_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_CLOUD_VISION_KEY not set")

        self.endpoint = "https://vision.googleapis.com/v1/images:annotate"
        self.free_only = os.environ.get("YO_GCV_FREE_ONLY", "1").strip().lower() not in {"0", "false", "no"}
        requested_profile = os.environ.get("YO_GCV_PROFILE", "lite").strip().lower() or "lite"
        self.profile = "lite" if self.free_only else requested_profile
        requested_daily_limit = int(os.environ.get("YO_GCV_DAILY_LIMIT", self.DEFAULT_DAILY_LIMIT))
        self.monthly_limit = int(os.environ.get("YO_GCV_MONTHLY_LIMIT", self.MONTHLY_FREE_UNITS))
        # Free-only mode never allows a daily pace that would overshoot the monthly free tier.
        safe_daily_limit = max(1, self.monthly_limit // 31)
        self.daily_limit = min(requested_daily_limit, safe_daily_limit) if self.free_only else requested_daily_limit
        self.units_per_image = 1 if self.profile == "lite" else 4

    def _features(self) -> list[dict]:
        if self.profile == "lite":
            return [{"type": "LABEL_DETECTION", "maxResults": 8}]
        return [
            {"type": "LABEL_DETECTION", "maxResults": 10},
            {"type": "LANDMARK_DETECTION", "maxResults": 5},
            {"type": "IMAGE_PROPERTIES"},
            {"type": "SAFE_SEARCH_DETECTION"},
        ]

    def _prepare_image(self, image_path: str, max_width: int = 2000) -> str:
        """Load image, resize if needed, return base64

        Args:
            image_path: path to image file
            max_width: max width for API (reduce payload)

        Returns:
            base64 encoded image
        """
        img = Image.open(image_path)

        # Resize if too large
        if img.width > max_width:
            ratio = max_width / img.width
            new_h = int(img.height * ratio)
            img = img.resize((max_width, new_h), Image.Resampling.LANCZOS)

        # Compress to JPEG for smaller payload
        jpg_bytes = io.BytesIO()
        img.save(jpg_bytes, format="JPEG", quality=80)
        img_data = jpg_bytes.getvalue()

        # Base64 encode
        return base64.standard_b64encode(img_data).decode("utf-8")

    def check_quota_warning(self, units_to_add: int) -> str:
        """Check if approaching quota limit

        Returns:
            warning message or empty string
        """
        budget = check_budget(
            units_per_image=units_to_add,
            daily_limit=self.daily_limit,
            monthly_limit=self.monthly_limit,
        )
        projected_usage = budget.month_units + units_to_add
        usage_percent = projected_usage / self.monthly_limit

        if usage_percent >= self.WARNING_THRESHOLD:
            remaining = self.monthly_limit - projected_usage
            warning = (
                f"\nWARNING: {projected_usage}/{self.monthly_limit} free units "
                f"({usage_percent:.1%}), today {budget.today_count}/{budget.daily_limit}"
            )
            warning += f"\n   Remaining this month: {max(0, remaining)} units"
            return warning
        return ""

    def analyze(self, image_path: str) -> Dict:
        """Analyze image with Cloud Vision API

        Args:
            image_path: path to image file

        Returns:
            dict with labels, landmarks, properties
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Check quota before API call
        budget = check_budget(
            units_per_image=self.units_per_image,
            daily_limit=self.daily_limit,
            monthly_limit=self.monthly_limit,
        )
        if not budget.allowed:
            return {
                "error": (
                    f"Vision budget blocked: today {budget.today_count}/{budget.daily_limit}, "
                    f"month {budget.month_units}/{budget.monthly_limit}"
                )
            }

        warning = self.check_quota_warning(self.units_per_image)
        if warning:
            print(warning)

        # Prepare image
        image_b64 = self._prepare_image(image_path)

        # Build request
        payload = {
            "requests": [
                {
                    "image": {"content": image_b64},
                    "features": self._features()
                }
            ]
        }

        # Call API
        try:
            resp = requests.post(
                f"{self.endpoint}?key={self.api_key}",
                json=payload,
                timeout=30
            )

            if resp.status_code != 200:
                error = resp.json().get("error", {})
                msg = error.get("message", f"HTTP {resp.status_code}")
                return {"error": msg}

            result = resp.json()
            response = result.get("responses", [{}])[0]

            if "error" in response:
                return {"error": response["error"]["message"]}

            consume_budget(units_per_image=self.units_per_image)

            # Extract data
            return {
                "success": True,
                "labels": [
                    {
                        "description": label["description"],
                        "score": label["score"]
                    }
                    for label in response.get("labelAnnotations", [])
                ],
                "landmarks": [
                    landmark["description"]
                    for landmark in response.get("landmarkAnnotations", [])
                ],
                "colors": self._extract_colors(response),
                "safe_search": response.get("safeSearchAnnotation", {}),
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def _extract_colors(response: Dict) -> list:
        """Extract dominant colors from image properties"""
        colors = []
        props = response.get("imagePropertiesAnnotation", {})
        for color_info in props.get("dominantColors", {}).get("colors", [])[:3]:
            rgb = color_info["color"]
            hex_color = f"#{int(rgb['red']):02x}{int(rgb['green']):02x}{int(rgb['blue']):02x}"
            colors.append({
                "hex": hex_color,
                "score": color_info["score"]
            })
        return colors

    def generate_metadata(self, image_path: str, location_hint: str = "") -> Dict:
        """Generate SEO metadata from Vision API analysis

        Args:
            image_path: path to image
            location_hint: location context (e.g., "petra")

        Returns:
            dict with alt, title, caption, description, keywords
        """
        analysis = self.analyze(image_path)

        if "error" in analysis:
            return {"error": analysis["error"]}

        # Build metadata from analysis
        labels = [l["description"] for l in analysis.get("labels", [])[:3]]
        landmarks = analysis.get("landmarks", [])

        # Construct semantic alt/title/description
        if landmarks:
            landmark = landmarks[0]
            alt = f"{landmark.lower().replace(' ', '-')}"
            title = landmark
            description = f"{landmark}. High-quality professional photography."
        elif labels:
            main_label = labels[0]
            extra = labels[1] if len(labels) > 1 else ""
            if location_hint:
                alt   = f"{location_hint.lower()}-{main_label.lower()}".replace(" ", "-")
                title = f"{location_hint.title()} — {main_label.title()}"
                description = f"{main_label.title()} in {location_hint.title()}. Professional photography."
            else:
                slug  = "-".join(l.lower().replace(" ", "-") for l in labels[:3])
                alt   = slug[:125]
                title = (f"{main_label.title()} — {extra.title()}" if extra else main_label.title())[:60]
                description = f"{main_label.title()}. Professional travel photography."
        else:
            alt = location_hint.lower().replace(" ", "-") if location_hint else "image"
            title = location_hint.title() if location_hint else "Image"
            description = f"Professional photograph from {location_hint}." if location_hint else "Image"

        return {
            "success": True,
            "alt": alt[:125],
            "title": title[:60],
            "caption": f"{title}",
            "description": description[:300],
            "keywords": labels + landmarks,
            "analysis": analysis,
        }


def generate_metadata_for_files(
    image_paths: list,
    location_hint: str = ""
) -> Dict:
    """Generate metadata for multiple images

    Args:
        image_paths: list of file paths
        location_hint: location context

    Returns:
        dict mapping filepath → metadata
    """
    api_key = os.environ.get("GOOGLE_CLOUD_VISION_KEY")
    if not api_key:
        print("⚠️  GOOGLE_CLOUD_VISION_KEY not set")
        return {}

    client = YOCloudVisionClient(api_key=api_key)
    results = {}

    # Pre-flight: show quota usage
    budget = check_budget(
        units_per_image=client.units_per_image,
        daily_limit=client.daily_limit,
        monthly_limit=client.MONTHLY_FREE_UNITS,
    )
    estimated_units = len(image_paths) * client.units_per_image
    estimated_total = budget.month_units + estimated_units
    print(f"  📊 Quota: {estimated_units} units for {len(image_paths)} images (profile={client.profile})")
    print(f"     Projected: {estimated_total}/{client.MONTHLY_FREE_UNITS} units")
    print(f"     Daily budget: {budget.today_count}/{client.daily_limit}")
    if estimated_total > client.MONTHLY_FREE_UNITS:
        overage = estimated_total - client.MONTHLY_FREE_UNITS
        print(f"     ⚠️  OVERAGE: {overage} units will incur charges")

    for i, img_path in enumerate(image_paths, 1):
        print(f"[{i}/{len(image_paths)}] Analyzing: {Path(img_path).name}")

        metadata = client.generate_metadata(img_path, location_hint=location_hint)

        if "error" in metadata:
            print(f"  ✗ Error: {metadata['error']}")
            results[img_path] = None
        else:
            print(f"  ✓ Alt: {metadata['alt']}")
            results[img_path] = metadata

    # Post-flight summary
    print(f"\n  ✅ Batch complete")
    print(f"     Usage: {client.monthly_usage}/{client.MONTHLY_FREE_UNITS} units")
    usage_percent = (client.monthly_usage / client.MONTHLY_FREE_UNITS) * 100
    print(f"     Progress: {usage_percent:.1f}% of monthly quota")

    return results


if __name__ == "__main__":
    # Test
    test_image = Path.home() / "Downloads" / "kalenderis.jpg"
    if test_image.exists():
        try:
            client = YOCloudVisionClient()
            result = client.generate_metadata(str(test_image), location_hint="petra")
            print("\n✅ Metadata generated:")
            import json
            print(json.dumps({k: v for k, v in result.items() if k != "analysis"}, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"✗ Error: {e}")
    else:
        print(f"Test image not found: {test_image}")
