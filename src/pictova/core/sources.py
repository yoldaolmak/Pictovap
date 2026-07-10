"""Image source orchestration: Article Input -> Candidate Images.

Reads a PublisherProfile's `image_sources` list and asks each configured
adapter for candidates, in order, until `count` candidates are collected
or every configured source has been tried.

Every adapter call is wrapped so a missing credential, network error, or
misconfiguration never raises here — it just yields zero candidates from
that source. This keeps `pictovap demo` credential-free and keeps `plan`
usable even when only some of a profile's sources are configured.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pictova.core.profile import PublisherProfile


def fetch_candidates(profile: PublisherProfile, query: str, count: int) -> List[Dict[str, Any]]:
    """Collect up to `count` real candidate images for `query`.

    Tries each adapter named in `profile.image_sources`, in order. Returns
    an empty list if no source is configured, unavailable, or uncredentialed
    — callers are expected to fall back to mock/demo candidates in that case.
    """
    candidates: List[Dict[str, Any]] = []
    for source_name in profile.image_sources:
        if len(candidates) >= count:
            break
        remaining = count - len(candidates)
        candidates.extend(_fetch_from_source(source_name, query, remaining))
    return candidates


def _fetch_from_source(source_name: str, query: str, count: int) -> List[Dict[str, Any]]:
    name = source_name.strip().lower()
    try:
        if name == "local":
            from pictova.providers.local import LocalFolderSource
            return LocalFolderSource().search_candidates(query, count)

        if name == "unsplash":
            from pictova.providers.unsplash import YOUnsplashDownloader
            return YOUnsplashDownloader().search_candidates(query, count)

        if name in ("deposit", "depositphotos"):
            from pictova.providers.deposit import DepositPhotosSource
            return DepositPhotosSource().search_candidates(query, count)

        if name == "openverse":
            from pictova.providers.openverse import OpenverseSource
            return OpenverseSource().search_candidates(query, count)

        if name == "pexels":
            from pictova.providers.pexels import PexelsSource
            return PexelsSource().search_candidates(query, count)

        # Unknown/unimplemented source name — skip rather than fail the
        # whole pipeline. See docs/contributing/good-first-issues.md for
        # sources that are documented but not yet built (e.g. Pixabay,
        # Wikimedia Commons).
        return []
    except Exception:
        return []


__all__ = ["fetch_candidates"]
