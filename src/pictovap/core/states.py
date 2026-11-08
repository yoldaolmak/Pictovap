"""Explicit state definitions and deterministic transitions across Pictovap.

All states inherit from `(str, Enum)` so JSON serialization, string
comparisons, and existing dict contracts remain 100% backward-compatible.
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable


class CandidateDecision(str, Enum):
    """Planner decision for a candidate image evaluated against an editorial slot."""

    SELECTED = "selected"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"

    def is_eligible(self, *, require_selected: bool = True) -> bool:
        """Check if this candidate can be assigned to a slot under current policy."""
        if self == CandidateDecision.REJECTED:
            return False
        if require_selected:
            return self == CandidateDecision.SELECTED
        return self in {CandidateDecision.SELECTED, CandidateDecision.NEEDS_REVIEW}


class AssignmentState(str, Enum):
    """Whether an editorial slot has an assigned candidate."""

    ASSIGNED = "assigned"
    NOT_ASSIGNED = "not_assigned"


class ConstraintKind(str, Enum):
    """Strictness category of an editorial intent constraint."""

    HARD = "hard"
    SOFT = "soft"


class ConstraintStatus(str, Enum):
    """Evaluation outcome for an editorial intent constraint."""

    PASSED = "passed"
    FAILED = "failed"


class CheckStatus(str, Enum):
    """Health check outcome vocabulary for audits and system diagnostics."""

    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"
    NOT_RUN = "not_run"


def aggregate_check_status(statuses: Iterable[str], *, strict: bool = False) -> str:
    """Aggregate a sequence of check statuses into a single summary status.

    - Any FAILED -> FAILED.
    - Any WARNING -> FAILED if strict else WARNING.
    - Otherwise -> PASSED.
    """
    normalized = [CheckStatus(s) for s in statuses]
    if any(st == CheckStatus.FAILED for st in normalized):
        return CheckStatus.FAILED.value
    if any(st == CheckStatus.WARNING for st in normalized):
        return CheckStatus.FAILED.value if strict else CheckStatus.WARNING.value
    return CheckStatus.PASSED.value


class SourceEpistemicState(str, Enum):
    """Observation status of a configured image source adapter."""

    OBSERVED = "observed"
    NOT_EVALUABLE = "not_evaluable"
    UNKNOWN = "unknown"


class SourceAttemptReason(str, Enum):
    """Canonical reasons recorded in SourceAttempt evidence."""

    NOT_QUERIED_COUNT_SATISFIED = "not_queried_count_satisfied"
    NOT_QUERIED_EXPLICIT_PROVIDER = "not_queried_explicit_provider"
    NOT_QUERIED_FIXTURE_RUN = "not_queried_fixture_run"
    UNIMPLEMENTED_SOURCE = "unimplemented_source"
    ADAPTER_ERROR = "adapter_error"


class ProviderRuntimeMode(str, Enum):
    """Runtime execution modes for provider plugins and fallbacks."""

    PLUGIN = "plugin"
    PROFILE = "profile"
    FALLBACK = "fallback"
    DEMO_FALLBACK = "demo-fallback"


class ReviewStatus(str, Enum):
    """Workflow state of a portable Decision Pack."""

    PENDING = "pending"
    REVIEWED = "reviewed"


class ReviewAction(str, Enum):
    """Human editorial actions supported on candidate proposals."""

    ACCEPT = "accept"
    REPLACE = "replace"
    REJECT = "reject"


class ApplicationStatus(str, Enum):
    """CMS application state of a Decision Pack."""

    NOT_APPLIED = "not_applied"


class PublishMode(str, Enum):
    """Runtime execution mode for publisher placement."""

    DRY_RUN = "dry-run"
    PUBLISH = "publish"


class PublishStatus(str, Enum):
    """Terminal outcome of a CMS publication attempt."""

    READY = "ready"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


def resolve_publish_status(*, dry_run: bool, placed_count: int, failed_count: int) -> str:
    """Resolve a publication outcome into an explicit PublishStatus value."""
    if dry_run:
        return PublishStatus.READY.value
    if failed_count == 0:
        return PublishStatus.COMPLETED.value
    if placed_count > 0:
        return PublishStatus.PARTIAL.value
    return PublishStatus.FAILED.value


class DoctorStatus(str, Enum):
    """Health check outcome for runtime plugin diagnostics."""

    READY = "ready"
    UNHEALTHY = "unhealthy"


class PlanDiffStatus(str, Enum):
    """Change status comparing two visual plans."""

    CHANGED = "changed"
    UNCHANGED = "unchanged"


class MediaIntegrityState(str, Enum):
    """Observed state of managed media items in a CMS post."""

    HEALTHY = "healthy"
    EMPTY = "empty"
    DRIFT = "drift"
    UNTRACKED = "untracked"
    INVALID = "invalid"


class MediaGuardStatus(str, Enum):
    """Action outcome for post media guard verification."""

    SUCCESS = "success"
    DRIFT = "drift"
    UNTRACKED = "untracked"
    FAILED = "failed"


def guard_status_for_state(state: str, *, failed: bool = False) -> str:
    """Map a media integrity state to a post media guard command status."""
    st = MediaIntegrityState(state)
    if failed or st == MediaIntegrityState.INVALID:
        return MediaGuardStatus.FAILED.value
    if st in {MediaIntegrityState.HEALTHY, MediaIntegrityState.EMPTY}:
        return MediaGuardStatus.SUCCESS.value
    if st == MediaIntegrityState.DRIFT:
        return MediaGuardStatus.DRIFT.value
    return MediaGuardStatus.UNTRACKED.value


__all__ = [
    "ApplicationStatus",
    "AssignmentState",
    "CandidateDecision",
    "CheckStatus",
    "ConstraintKind",
    "ConstraintStatus",
    "DoctorStatus",
    "MediaGuardStatus",
    "MediaIntegrityState",
    "PlanDiffStatus",
    "ProviderRuntimeMode",
    "PublishMode",
    "PublishStatus",
    "ReviewAction",
    "ReviewStatus",
    "SourceAttemptReason",
    "SourceEpistemicState",
    "aggregate_check_status",
    "guard_status_for_state",
    "resolve_publish_status",
]
