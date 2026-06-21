"""Yoldaolmak profile defaults."""

from __future__ import annotations

import os
from typing import Dict


PROFILE_NAME = "yoldaolmak"
DEFAULT_LANGUAGE = "tr"
DEFAULT_FILTER_PROFILE = "yoldaolmak"


def apply_environment() -> Dict[str, str]:
    os.environ.setdefault("YO_IMAGE_FILTER_PROFILE", DEFAULT_FILTER_PROFILE)
    return {
        "profile": PROFILE_NAME,
        "language": DEFAULT_LANGUAGE,
        "filter_profile": os.environ.get("YO_IMAGE_FILTER_PROFILE", DEFAULT_FILTER_PROFILE),
    }
