#!/usr/bin/env python3
"""Runnable skeleton for a custom image source adapter.

An image source adapter supplies candidate images to the Fit Score stage.
The contract is `pictovap.core.adapters.ImageSourceAdapter` — a
`typing.Protocol`, so you don't inherit from anything; you just implement
`search_candidates(query, count)` with the documented candidate shape.

This example implements the contract against a plain JSON manifest file,
so it runs with zero credentials and zero network access:

    python examples/adapters/custom_image_source.py

Replace the manifest lookup with your real source (a stock photo API, a
DAM, an internal service). Two rules carry over to any real adapter:

1. Constructing the adapter must never require credentials — read them
   from environment variables inside `search_candidates`, and return an
   empty list when they're missing. That keeps the credential-free demo
   and partially-configured profiles working.
2. Every candidate must carry its real license and attribution — the
   Provenance Pack stage records them as the audit trail.

See docs/contributing/adapters.md for the checklist to ship one in
`src/pictovap/providers/`.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from pictovap.core.adapters import ImageSourceAdapter


class ManifestImageSource:
    """Serves candidates from a JSON manifest of pre-described images.

    The manifest maps keywords to image records. A real adapter would
    query an external API here instead.
    """

    def __init__(self, manifest_path: str):
        self.manifest_path = Path(manifest_path)

    def search_candidates(self, query: str, count: int) -> List[Dict[str, Any]]:
        if not self.manifest_path.exists():
            return []  # degrade gracefully, never raise from a misconfig

        records = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        query_terms = {term.lower() for term in query.split()}

        matches = []
        for record in records:
            keywords = {keyword.lower() for keyword in record.get("keywords", [])}
            if query_terms & keywords:
                matches.append(self._to_candidate(record))
            if len(matches) >= count:
                break
        return matches

    def _to_candidate(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Map a source record to Pictovap's candidate shape.

        Every key below is required by the contract — see the
        `ImageSourceAdapter.search_candidates` docstring.
        """
        return {
            "id": record["id"],
            "filename": record["filename"],
            "provider": "manifest-example",
            "source_type": "local",
            "local_path": record.get("path"),
            "source_url": None,
            "license": record.get("license", "unknown"),
            "attribution": record.get("attribution"),
            "keywords": record.get("keywords", []),
            "width": record.get("width", 0),
            "height": record.get("height", 0),
        }


SAMPLE_MANIFEST = [
    {
        "id": "m-001",
        "filename": "morning-market.webp",
        "path": "/library/morning-market.webp",
        "license": "cc0",
        "attribution": None,
        "keywords": ["market", "food", "city"],
        "width": 1920,
        "height": 1280,
    },
    {
        "id": "m-002",
        "filename": "river-bridge.webp",
        "path": "/library/river-bridge.webp",
        "license": "cc-by",
        "attribution": "Jane Photographer",
        "keywords": ["river", "bridge", "travel"],
        "width": 2048,
        "height": 1365,
    },
]


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        manifest = Path(tmp) / "manifest.json"
        manifest.write_text(json.dumps(SAMPLE_MANIFEST), encoding="utf-8")

        source = ManifestImageSource(str(manifest))

        # The Protocol is runtime-checkable: this is how the test suite
        # validates adapters, and yours should pass the same check.
        assert isinstance(source, ImageSourceAdapter)
        print("contract check: ManifestImageSource satisfies ImageSourceAdapter")

        for query in ("food market", "river crossing", "nothing matches this"):
            results = source.search_candidates(query, count=5)
            print(f"query {query!r}: {len(results)} candidate(s)")
            for candidate in results:
                print(f"  - {candidate['filename']} ({candidate['license']})")


if __name__ == "__main__":
    main()
