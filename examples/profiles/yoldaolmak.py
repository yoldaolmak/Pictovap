"""Example: yoldaolmak.com's original site profile (pre-PublisherProfile).

This is a real production example, kept for reference only. It predates
`PublisherProfile.from_yaml` (see `examples/profiles/sample-publisher.yaml`
for the current, supported profile format) and is not imported by the
package anymore. It shows the original per-site environment convention
this project's publisher profile concept grew out of.
"""

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
