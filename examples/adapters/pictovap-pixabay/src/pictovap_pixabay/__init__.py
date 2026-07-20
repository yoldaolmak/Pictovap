"""Pixabay image-source adapter for Pictovap."""

from __future__ import annotations

from typing import Any, Dict, List


class PixabaySource:
    """Return image candidates from Pixabay."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def search_candidates(self, query: str, count: int) -> List[Dict[str, Any]]:
        # Replace this empty result with the provider API integration.
        # Missing credentials must remain a safe empty-result path.
        if not self.api_key:
            return []
        return []


__all__ = ["PixabaySource"]
