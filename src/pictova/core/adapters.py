"""
Formal adapter contracts for Pictovap.

Pictovap's core pipeline (Visual Brief -> Fit Score -> Provenance Pack ->
CMS Placement) has no dependency on any specific image provider or CMS.
Everything external plugs in through one of the protocols defined here.

These are `typing.Protocol` classes: an adapter does not need to inherit
from them, it only needs to implement the matching methods (structural
typing / duck typing). They exist so that:

  - the required shape of an adapter is documented in one importable place
  - `isinstance(obj, ImageSourceAdapter)` works for runtime checks
  - IDEs and type checkers can validate third-party adapters

See docs/adapters/overview.md for the conceptual model, and
docs/contributing/adapters.md for a walkthrough of writing a new one.
"""

from __future__ import annotations

from typing import Any, Dict, List, Protocol, runtime_checkable

from pictova.core.primitives import CMSPlacement


@runtime_checkable
class ImageSourceAdapter(Protocol):
    """Supplies candidate images to the Fit Score stage.

    Implementations may call a local folder, a stock photo API, a DAM, or
    any other source. They must never require credentials to import or
    construct — missing credentials should surface as an empty result or
    a clear error only when a search is actually attempted, so the
    credential-free demo path keeps working.
    """

    def search_candidates(self, query: str, count: int) -> List[Dict[str, Any]]:
        """Return up to `count` candidate images matching `query`.

        Each candidate dict must contain at least:
            id, filename, provider, source_type ("local" | "api" | "url"),
            local_path (str | None), source_url (str | None), license,
            attribution (str | None), keywords (list[str]), width, height
        """
        ...


@runtime_checkable
class CMSAdapter(Protocol):
    """Consumes a CMS Placement plan and executes it against a real CMS.

    A CMS adapter translates Pictovap's CMS-agnostic placement plan into
    the target platform's native representation (e.g. a WordPress
    Gutenberg block, a Ghost mobiledoc card, a Strapi component).
    """

    def place(self, placement: CMSPlacement) -> Dict[str, Any]:
        """Execute the placement plan. Returns a dict with at least:
            placed (list), failed (list), warnings (list)
        """
        ...


@runtime_checkable
class ReportRenderer(Protocol):
    """Renders a visual plan (JSON-shaped dict) into a human- or
    machine-facing output format (Markdown, HTML, a CMS payload, etc.).
    """

    def render(self, plan: Dict[str, Any]) -> str:
        """Return the rendered report as a string."""
        ...


__all__ = ["ImageSourceAdapter", "CMSAdapter", "ReportRenderer"]
