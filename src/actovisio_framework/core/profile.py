"""Versioned Publisher Profile contract and YAML loader."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml


PROFILE_SCHEMA_VERSION = 1
_PROFILE_ID = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_LANGUAGE = re.compile(r"^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
_RULE_FIELDS = (
    "output_rules",
    "filename_rules",
    "alt_text_rules",
    "caption_rules",
    "editorial_preferences",
)
_FIELDS = frozenset({
    "schema_version", "profile_id", "brand_name", "cms_type", "language",
    "language_mode", "image_sources", "output_rules", "filename_rules",
    "alt_text_rules", "caption_rules", "editorial_preferences", "forbidden_patterns",
})


class PublisherProfileError(ValueError):
    """Raised when a publisher profile does not satisfy the public contract."""


def _non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PublisherProfileError(f"'{field_name}' must be a non-empty string")
    return value.strip()


def _string_list(value: Any, field_name: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        requirement = "a list of strings" if allow_empty else "a non-empty list of strings"
        raise PublisherProfileError(f"'{field_name}' must be {requirement}")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise PublisherProfileError(f"'{field_name}' must contain only non-empty strings")
    return [item.strip() for item in value]


def _rule_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise PublisherProfileError(f"'{field_name}' must be a mapping")
    if not all(isinstance(key, str) and key.strip() for key in value):
        raise PublisherProfileError(f"'{field_name}' keys must be non-empty strings")
    return dict(value)


@dataclass
class PublisherProfile:
    """Stable, CMS-neutral configuration for one publisher deployment.

    YAML is the public interchange format. The dataclass remains convenient for
    Python callers, while :meth:`from_yaml` and :meth:`from_mapping` enforce
    the v1 contract before a plan can run.
    """

    profile_id: str
    brand_name: str
    cms_type: str = "wordpress"
    language: str = "en"
    language_mode: str = "fallback"
    image_sources: list[str] = field(default_factory=lambda: ["local", "unsplash"])
    output_rules: dict[str, Any] = field(default_factory=dict)
    filename_rules: dict[str, Any] = field(default_factory=dict)
    alt_text_rules: dict[str, Any] = field(default_factory=dict)
    caption_rules: dict[str, Any] = field(default_factory=dict)
    editorial_preferences: dict[str, Any] = field(default_factory=dict)
    forbidden_patterns: list[str] = field(default_factory=list)
    schema_version: int = PROFILE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Raise :class:`PublisherProfileError` unless this is a valid v1 profile."""
        if self.schema_version != PROFILE_SCHEMA_VERSION:
            raise PublisherProfileError(
                f"Unsupported profile schema_version {self.schema_version!r}; "
                f"expected {PROFILE_SCHEMA_VERSION}"
            )
        self.profile_id = _non_empty_string(self.profile_id, "profile_id")
        if not _PROFILE_ID.fullmatch(self.profile_id):
            raise PublisherProfileError(
                "'profile_id' must start with a lowercase letter and contain only "
                "lowercase letters, numbers, or hyphens"
            )
        self.brand_name = _non_empty_string(self.brand_name, "brand_name")
        self.cms_type = _non_empty_string(self.cms_type, "cms_type")
        self.language = _non_empty_string(self.language, "language").lower()
        if not _LANGUAGE.fullmatch(self.language):
            raise PublisherProfileError("'language' must be an ISO-style language tag such as 'en' or 'pt-BR'")
        if self.language_mode not in {"fallback", "override"}:
            raise PublisherProfileError("'language_mode' must be 'fallback' or 'override'")
        self.image_sources = _string_list(self.image_sources, "image_sources")
        self.forbidden_patterns = _string_list(self.forbidden_patterns, "forbidden_patterns", allow_empty=True)
        for field_name in _RULE_FIELDS:
            setattr(self, field_name, _rule_mapping(getattr(self, field_name), field_name))

    @classmethod
    def get_default_profile(cls) -> "PublisherProfile":
        """Return the credential-free demo profile."""
        return cls(profile_id="demo", brand_name="Demo Publisher")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "PublisherProfile":
        """Build a validated v1 profile from parsed YAML or a Python mapping."""
        if not isinstance(data, Mapping):
            raise PublisherProfileError("Publisher profile root must be a mapping")
        unknown = set(data) - _FIELDS
        if unknown:
            raise PublisherProfileError(f"Unknown publisher profile field(s): {', '.join(sorted(unknown))}")
        if "schema_version" not in data:
            raise PublisherProfileError("'schema_version' is required; set it to 1 for the current contract")
        required = ("profile_id", "brand_name")
        missing = [field_name for field_name in required if field_name not in data]
        if missing:
            raise PublisherProfileError(f"Missing required publisher profile field(s): {', '.join(missing)}")
        return cls(
            schema_version=data["schema_version"],
            profile_id=data["profile_id"],
            brand_name=data["brand_name"],
            cms_type=data.get("cms_type", "wordpress"),
            language=data.get("language", "en"),
            language_mode=data.get("language_mode", "fallback"),
            image_sources=data.get("image_sources", ["local", "unsplash"]),
            output_rules=data.get("output_rules", {}),
            filename_rules=data.get("filename_rules", {}),
            alt_text_rules=data.get("alt_text_rules", {}),
            caption_rules=data.get("caption_rules", {}),
            editorial_preferences=data.get("editorial_preferences", {}),
            forbidden_patterns=data.get("forbidden_patterns", []),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PublisherProfile":
        """Load and validate a Publisher Profile v1 YAML document."""
        try:
            data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise PublisherProfileError(f"Invalid YAML in publisher profile '{path}': {exc}") from exc
        return cls.from_mapping(data)
