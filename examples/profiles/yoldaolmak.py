"""Example: yoldaolmak.com's original site profile (pre-PublisherProfile).

This is a real production example, kept for reference only. It predates
`PublisherProfile.from_yaml` (see `examples/profiles/sample-publisher.yaml`
for the current, supported profile format) and is not imported by the
package anymore. It shows how a site-specific Python profile can expose the
same canonical Pictovap environment naming.
"""

from __future__ import annotations

import os
from typing import Dict


PROFILE_NAME = "yoldaolmak"
DEFAULT_LANGUAGE = "tr"
DEFAULT_FILTER_PROFILE = "yoldaolmak"


def apply_environment() -> Dict[str, str]:
    os.environ.setdefault("PICTOVAP_IMAGE_FILTER_PROFILE", DEFAULT_FILTER_PROFILE)
    return {
        "profile": PROFILE_NAME,
        "language": DEFAULT_LANGUAGE,
        "filter_profile": os.environ.get("PICTOVAP_IMAGE_FILTER_PROFILE", DEFAULT_FILTER_PROFILE),
    }
