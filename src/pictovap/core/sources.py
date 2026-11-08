"""Image source orchestration: Article Input -> Candidate Images.

Reads a PublisherProfile's `image_sources` list and asks each configured
adapter for candidates, in order, until `count` candidates are collected
or every configured source has been tried.

Every adapter call is wrapped so a missing credential, network error, or
misconfiguration never raises here — it just yields zero candidates from
that source. This keeps `pictovap demo` credential-free and keeps `plan`
usable even when only some of a profile's sources are configured.

Degrading quietly is not the same as degrading silently. Each attempt is
recorded, so a plan can distinguish a source that ran and found nothing from
one that could not be evaluated at all. Without that record, an empty result
would be indistinguishable from a failure, and a plan would imply editorial
coverage it never actually observed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from pictovap.core.profile import PublisherProfile
from pictovap.core.states import SourceAttemptReason, SourceEpistemicState


# Epistemic states, matching the vocabulary used across Pictovap contracts:
#   observed       the adapter ran; `candidates` is what it actually returned
#   not_evaluable  the adapter could not produce a conclusion at all
#   unknown        the source was not queried, so its result is not known
OBSERVED = SourceEpistemicState.OBSERVED.value
NOT_EVALUABLE = SourceEpistemicState.NOT_EVALUABLE.value
UNKNOWN = SourceEpistemicState.UNKNOWN.value


@dataclass(frozen=True)
class SourceAttempt:
    """What one configured image source contributed to a plan, and why."""

    source: str
    state: str
    candidates: int = 0
    reason: str | None = None
    error_type: str | None = None

    def __post_init__(self) -> None:
        try:
            st = SourceEpistemicState(self.state)
        except ValueError:
            raise ValueError(f"Invalid SourceAttempt state: {self.state!r}")
        object.__setattr__(self, "state", st.value)

        if self.candidates < 0:
            raise ValueError("SourceAttempt.candidates cannot be negative")

        if st == SourceEpistemicState.OBSERVED:
            if self.error_type is not None:
                raise ValueError("Observed SourceAttempt cannot carry error_type")
        elif st == SourceEpistemicState.NOT_EVALUABLE:
            if self.candidates != 0:
                raise ValueError("not_evaluable SourceAttempt must have 0 candidates")
            if not self.reason or not str(self.reason).strip():
                raise ValueError("not_evaluable SourceAttempt requires a reason")
        elif st == SourceEpistemicState.UNKNOWN:
            if self.candidates != 0:
                raise ValueError("unknown SourceAttempt must have 0 candidates")
            if self.error_type is not None:
                raise ValueError("unknown SourceAttempt cannot carry error_type")
            if not self.reason or not str(self.reason).strip():
                raise ValueError("unknown SourceAttempt requires a reason")

    def to_dict(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "source": self.source,
            "state": self.state,
            "candidates": self.candidates,
        }
        if self.reason:
            record["reason"] = self.reason
        if self.error_type:
            record["error_type"] = self.error_type
        return record


@dataclass(frozen=True)
class SourceFetchResult:
    """Collected candidates plus the per-source evidence behind them."""

    candidates: List[Dict[str, Any]]
    attempts: tuple[SourceAttempt, ...]

    def to_dict(self) -> list[dict[str, Any]]:
        return [attempt.to_dict() for attempt in self.attempts]


def fetch_candidates(profile: PublisherProfile, query: str, count: int) -> List[Dict[str, Any]]:
    """Collect up to `count` real candidate images for `query`.

    Returns an empty list if no source is configured, unavailable, or
    uncredentialed — callers are expected to fall back to fixture candidates in
    that case. Use `fetch_candidates_with_evidence()` when the caller needs to
    record *why* a source contributed nothing.
    """
    return fetch_candidates_with_evidence(profile, query, count).candidates


def fetch_candidates_with_evidence(
    profile: PublisherProfile,
    query: str,
    count: int,
) -> SourceFetchResult:
    """Collect candidates and one evidence record per configured source."""
    candidates: List[Dict[str, Any]] = []
    attempts: List[SourceAttempt] = []
    for source_name in profile.image_sources:
        if len(candidates) >= count:
            attempts.append(SourceAttempt(
                source=source_name,
                state=UNKNOWN,
                reason="not_queried_count_satisfied",
            ))
            continue
        attempt, found = _fetch_from_source(source_name, query, count - len(candidates))
        attempts.append(attempt)
        candidates.extend(found)
    return SourceFetchResult(candidates=candidates, attempts=tuple(attempts))


_ADAPTERS = {
    "local": ("pictovap.providers.local", "LocalFolderSource"),
    "unsplash": ("pictovap.providers.unsplash", "UnsplashSource"),
    "deposit": ("pictovap.providers.deposit", "DepositPhotosSource"),
    "depositphotos": ("pictovap.providers.deposit", "DepositPhotosSource"),
    "openverse": ("pictovap.providers.openverse", "OpenverseSource"),
    "pexels": ("pictovap.providers.pexels", "PexelsSource"),
}


def _fetch_from_source(
    source_name: str,
    query: str,
    count: int,
) -> tuple[SourceAttempt, List[Dict[str, Any]]]:
    name = source_name.strip().lower()
    target = _ADAPTERS.get(name)
    if target is None:
        # Unknown/unimplemented source name — skip rather than fail the whole
        # pipeline. See docs/contributing/good-first-issues.md for sources that
        # are documented but not yet built (e.g. Pixabay, Wikimedia Commons).
        return SourceAttempt(
            source=source_name,
            state=NOT_EVALUABLE,
            reason="unimplemented_source",
        ), []

    module_name, class_name = target
    try:
        import importlib

        adapter_class = getattr(importlib.import_module(module_name), class_name)
        found = adapter_class().search_candidates(query, count)
    except Exception as exc:
        # Record the failure class only. An adapter's message can carry a
        # request URL with an embedded API key, and this record is serialized
        # into a plan that gets committed, shared, and pasted into issues.
        return SourceAttempt(
            source=source_name,
            state=NOT_EVALUABLE,
            reason="adapter_error",
            error_type=type(exc).__name__,
        ), []

    return SourceAttempt(
        source=source_name,
        state=OBSERVED,
        candidates=len(found),
    ), list(found)


__all__ = [
    "NOT_EVALUABLE",
    "OBSERVED",
    "SourceAttempt",
    "SourceAttemptReason",
    "SourceEpistemicState",
    "SourceFetchResult",
    "UNKNOWN",
    "fetch_candidates",
    "fetch_candidates_with_evidence",
]
