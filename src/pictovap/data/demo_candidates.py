"""Deterministic candidate fixtures for the credential-free demo.

These candidates are the demo's guarantee, not a hidden default: they are
passed explicitly into the planner by whoever wants a fallback, so the
planning engine itself carries no knowledge of demo data.
"""

from __future__ import annotations

from typing import Any


MOCK_CANDIDATES: list[dict[str, Any]] = [
    {
        "id": "img-backpack-01",
        "filename": "minimal-backpack.jpg",
        "provider": "local",
        "source_type": "local",
        "local_path": "examples/assets/minimal-backpack.jpg",
        "license": "CC0",
        "attribution": None,
        "keywords": ["backpack", "travel", "minimalist", "packing"],
        "width": 1920,
        "height": 1280,
    },
    {
        "id": "img-forest-02",
        "filename": "forest-path.jpg",
        "provider": "local",
        "source_type": "local",
        "local_path": "examples/assets/forest-path.jpg",
        "license": "CC0",
        "attribution": None,
        "keywords": ["forest", "nature", "path", "serenity", "trees"],
        "width": 1600,
        "height": 1067,
    },
    {
        "id": "img-generic-03",
        "filename": "generic-stock.jpg",
        "provider": "stock",
        "source_type": "api",
        "local_path": None,
        "source_url": "https://example.com/generic-stock.jpg",
        "license": "editorial",
        "attribution": "Example Stock Co.",
        "keywords": ["map", "tourist", "generic"],
        "width": 800,
        "height": 600,
    },
    {
        "id": "img-lowres-04",
        "filename": "blurry-phone.jpg",
        "provider": "local",
        "source_type": "local",
        "local_path": "examples/assets/blurry-phone.jpg",
        "license": "owned",
        "attribution": None,
        "keywords": ["phone", "blurry", "travel"],
        "width": 320,
        "height": 240,
    },
    {
        "id": "img-sunset-05",
        "filename": "sunset-mountains.jpg",
        "provider": "unsplash_mock",
        "source_type": "api",
        "local_path": None,
        "source_url": "https://unsplash.com/photos/mock-sunset",
        "license": "unsplash",
        "attribution": "Photo by Jane Doe on Unsplash",
        "keywords": ["sunset", "mountains", "nature", "travel", "landscape"],
        "width": 2400,
        "height": 1600,
    },
    {
        "id": "img-lake-06",
        "filename": "quiet-lake.jpg",
        "provider": "local",
        "source_type": "local",
        "local_path": "examples/assets/quiet-lake.jpg",
        "license": "CC0",
        "attribution": None,
        "keywords": ["lake", "nature", "serenity", "travel", "landscape"],
        "width": 1800,
        "height": 1200,
    },
]


__all__ = ["MOCK_CANDIDATES"]
