"""Wikimedia image-source adapter for Pictovap."""

from __future__ import annotations

from typing import Any, Dict, List


class WikimediaSource:
    """Return image candidates from Wikimedia."""

    def search_candidates(self, query: str, count: int) -> List[Dict[str, Any]]:
        # Replace this empty result with the provider API integration.
        # Wikimedia Commons does not require an API key.
        return []


__all__ = ["WikimediaSource"]
