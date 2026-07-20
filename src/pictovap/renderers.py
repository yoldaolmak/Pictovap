"""Built-in renderers for human review of a Pictovap visual plan."""

from __future__ import annotations

from html import escape
from typing import Any


class MarkdownReportRenderer:
    """Render the established Markdown editor report."""

    def render(self, plan: dict[str, Any]) -> str:
        # Kept in demo for backward compatibility with the original report CLI.
        from pictovap.demo import generate_markdown_report

        return generate_markdown_report(plan)


class HTMLReportRenderer:
    """Render a self-contained, dependency-free HTML editor report."""

    def render(self, plan: dict[str, Any]) -> str:
        brief = plan.get("visual_brief", {})
        profile = plan.get("profile", {})
        packs = plan.get("provenance_packs", [])
        placement = plan.get("cms_placement", {})
        title = escape(str(brief.get("article_title", "Untitled article")))
        publisher = escape(str(profile.get("brand", "Unknown publisher")))
        image_rows = "".join(
            "<tr>"
            f"<td>{escape(str(pack.get('slot_id', '')))}</td>"
            f"<td>{escape(str(pack.get('provider', '')))}</td>"
            f"<td>{escape(str(pack.get('license_status', 'unknown')))}</td>"
            f"<td>{escape(str(pack.get('generated_alt_text', '')))}</td>"
            "</tr>"
            for pack in packs
        ) or "<tr><td colspan=\"4\">No images selected.</td></tr>"
        placement_rows = "".join(
            "<li>"
            f"{escape(str(item.get('image_role', 'image')))}: "
            f"{escape(str(item.get('placement_strategy', 'placement')))} "
            f"{escape(str(item.get('target_section') or 'top'))}"
            "</li>"
            for item in placement.get("placements", [])
        ) or "<li>No CMS placements planned.</li>"
        style = (
            "body{font:16px/1.5 system-ui,sans-serif;max-width:960px;margin:40px auto;"
            "padding:0 20px;color:#1d1d1f}table{border-collapse:collapse;width:100%}"
            "th,td{border:1px solid #d2d2d7;padding:9px;text-align:left}"
            "th{background:#f5f5f7}h1{margin-bottom:0}.meta{color:#6e6e73}"
        )
        return f"""<!doctype html>
<html lang=\"en\">
<head><meta charset=\"utf-8\"><title>Pictovap Visual Plan — {title}</title>
<style>{style}</style></head>
<body><h1>Pictovap Visual Plan</h1><p class=\"meta\">{title} · {publisher}</p>
<h2>Selected Images</h2><table><thead><tr><th>Slot</th><th>Provider</th><th>License</th><th>Alt text</th></tr></thead>
<tbody>{image_rows}</tbody></table>
<h2>CMS Placement Plan</h2><ul>{placement_rows}</ul></body></html>"""


__all__ = ["HTMLReportRenderer", "MarkdownReportRenderer"]
