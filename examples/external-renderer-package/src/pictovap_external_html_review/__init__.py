"""A standalone Pictovap HTML review renderer plugin."""

from __future__ import annotations

from html import escape
from typing import Any


class ExternalHTMLReviewRenderer:
    """Render selected images and placement instructions as portable HTML."""

    def render(self, plan: dict[str, Any]) -> str:
        brief = plan.get("visual_brief", {})
        placement = plan.get("cms_placement", {})
        title = escape(str(brief.get("article_title", "Untitled article")))
        rows = "".join(
            "<li>"
            f"{escape(str(item.get('image_role', 'image')))}: "
            f"{escape(str(item.get('placement_strategy', 'placement')))} "
            f"{escape(str(item.get('target_section') or 'top'))}"
            "</li>"
            for item in placement.get("placements", [])
        ) or "<li>No placement instructions.</li>"
        return (
            "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<title>Pictovap review — {title}</title></head><body>"
            f"<h1>{title}</h1><h2>Placement review</h2><ul>{rows}</ul>"
            "</body></html>"
        )


__all__ = ["ExternalHTMLReviewRenderer"]
