"""Hugo CMS adapter example for Pictovap."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import re
from typing import Any

from pictovap.core.primitives import CMSPlacement, PlacementInstruction


@dataclass(frozen=True)
class _ResolvedArticle:
    path: Path
    existed: bool


class HugoAdapter:
    """Write Pictovap placement instructions as Hugo figure shortcodes."""

    __test__ = False

    def __init__(
        self,
        content_dir: str | None = None,
        assets_prefix: str = "/images/pictovap",
        shortcode_name: str = "figure",
    ) -> None:
        self.content_dir = Path(content_dir).expanduser().resolve() if content_dir else None
        self.assets_prefix = "/" + assets_prefix.strip("/")
        self.shortcode_name = shortcode_name

    def place(self, placement: CMSPlacement) -> dict[str, list[dict[str, Any]] | list[str]]:
        warnings: list[str] = []
        placed: list[dict[str, Any]] = []
        failed: list[dict[str, str]] = []

        if self.content_dir is None:
            return {
                "placed": placed,
                "failed": failed,
                "warnings": ["content_dir is not configured; no Hugo files were written"],
            }

        resolved = self._resolve_article(placement.article_id)
        if resolved is None:
            return {
                "placed": placed,
                "failed": [{
                    "article_id": placement.article_id,
                    "error": "article_id must resolve inside content_dir",
                }],
                "warnings": warnings,
            }

        text = resolved.path.read_text(encoding="utf-8") if resolved.existed else ""
        for instruction in placement.placements:
            try:
                text = self._upsert_shortcode(text, instruction)
                placed.append({
                    "slot_id": instruction.slot_id,
                    "article_path": str(resolved.path),
                    "target_section": instruction.target_section,
                })
            except ValueError as exc:
                failed.append({"slot_id": instruction.slot_id, "error": str(exc)})

        if placed and not failed:
            resolved.path.parent.mkdir(parents=True, exist_ok=True)
            resolved.path.write_text(text, encoding="utf-8")
        elif not placed:
            warnings.append("No placement instructions were applied")

        return {"placed": placed, "failed": failed, "warnings": warnings}

    def _resolve_article(self, article_id: str) -> _ResolvedArticle | None:
        assert self.content_dir is not None
        article_path = Path(article_id)
        if article_path.is_absolute():
            return None
        if article_path.suffix.lower() != ".md":
            article_path = article_path.with_suffix(".md")
        resolved = (self.content_dir / article_path).resolve()
        try:
            resolved.relative_to(self.content_dir)
        except ValueError:
            return None
        return _ResolvedArticle(path=resolved, existed=resolved.exists())

    def _upsert_shortcode(self, text: str, instruction: PlacementInstruction) -> str:
        if not instruction.output_path:
            raise ValueError("output_path is required")

        start = f"<!-- pictovap:{instruction.slot_id}:start -->"
        end = f"<!-- pictovap:{instruction.slot_id}:end -->"
        block = f"{start}\n{self._shortcode(instruction)}\n{end}"
        pattern = re.compile(
            rf"{re.escape(start)}.*?{re.escape(end)}",
            flags=re.DOTALL,
        )
        if pattern.search(text):
            return pattern.sub(block, text)

        lines = text.splitlines()
        target = instruction.target_section.strip().casefold()
        if target:
            for index, line in enumerate(lines):
                heading = line.lstrip("#").strip().casefold()
                if line.startswith("#") and heading == target:
                    lines[index + 1:index + 1] = ["", block]
                    return "\n".join(lines).rstrip() + "\n"

        if text.strip():
            return text.rstrip() + "\n\n" + block + "\n"
        return block + "\n"

    def _shortcode(self, instruction: PlacementInstruction) -> str:
        filename = Path(instruction.output_path).name
        if not filename:
            raise ValueError("output_path must include a filename")
        src = f"{self.assets_prefix}/{filename}"
        attrs = {
            "src": src,
            "alt": instruction.alt_text,
            "caption": instruction.caption,
        }
        serialized = " ".join(
            f'{key}="{escape(value, quote=True)}"'
            for key, value in attrs.items()
            if value
        )
        return f"{{{{< {self.shortcode_name} {serialized} >}}}}"


__all__ = ["HugoAdapter"]
