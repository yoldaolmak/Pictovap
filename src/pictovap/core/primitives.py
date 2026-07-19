"""
Core domain primitives for Pictovap.

These dataclasses define the structured contracts that move through
the visual finishing pipeline:

    Visual Brief → Fit Score → Provenance Pack → CMS Placement

All primitives are serializable to JSON via their to_dict() methods.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from html.parser import HTMLParser
import re
from typing import Any, Dict, List, Optional


class LicenseType(str, Enum):
    CC0 = "cc0"
    CC_BY = "cc_by"
    CC_BY_SA = "cc_by_sa"
    CC_BY_NC = "cc_by_nc"
    CC_BY_NC_SA = "cc_by_nc_sa"
    CC_BY_ND = "cc_by_nd"
    CC_BY_NC_ND = "cc_by_nc_nd"
    PDM = "pdm"
    SAMPLING_PLUS = "sampling_plus"
    NC_SAMPLING_PLUS = "nc_sampling_plus"
    OWNED = "owned"
    UNSPLASH = "unsplash"
    PEXELS = "pexels"
    EDITORIAL = "editorial"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: Any) -> "LicenseType":
        if isinstance(value, cls):
            return value
        normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "cc0_1.0": cls.CC0, "public_domain": cls.CC0,
            "creative_commons": cls.CC_BY, "by": cls.CC_BY,
            "cc_by_4.0": cls.CC_BY,
            "by_sa": cls.CC_BY_SA, "cc_by_sa_4.0": cls.CC_BY_SA,
            "by_nc": cls.CC_BY_NC, "cc_by_nc_4.0": cls.CC_BY_NC,
            "by_nc_sa": cls.CC_BY_NC_SA,
            "by_nd": cls.CC_BY_ND,
            "by_nc_nd": cls.CC_BY_NC_ND,
            "sampling+": cls.SAMPLING_PLUS,
            "nc_sampling+": cls.NC_SAMPLING_PLUS,
        }
        try:
            return cls(normalized)
        except ValueError:
            return aliases.get(normalized, cls.UNKNOWN)


@dataclass
class VisualBrief:
    """
    A structured visual requirement extracted from article content.
    Dictates what kind of imagery the article needs.

    Generated from article analysis (markdown parsing, CMS fetch, etc.).
    """
    article_title: str
    article_id: Optional[str] = None
    article_language: str = "en"
    topic: str = ""
    detected_location: Optional[str] = None
    sections: List[Dict[str, str]] = field(default_factory=list)
    image_slots: List[Dict[str, Any]] = field(default_factory=list)
    avoid_list: List[str] = field(default_factory=list)
    editorial_notes: str = ""
    confidence: float = 0.0
    source_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "article_title": self.article_title,
            "article_id": self.article_id,
            "article_language": self.article_language,
            "topic": self.topic,
            "detected_location": self.detected_location,
            "sections": self.sections,
            "image_slots": self.image_slots,
            "avoid_list": self.avoid_list,
            "editorial_notes": self.editorial_notes,
            "confidence": self.confidence,
            "source_path": self.source_path,
        }

    @classmethod
    def from_markdown(cls, path: str, fallback_lang: str = "en") -> "VisualBrief":
        """Parse a markdown file and extract a VisualBrief.

        This is a deterministic, rule-based parser. It does not use AI.
        It extracts headings and builds image slots from the document structure.
        """
        from pathlib import Path
        from pictovap.core.language import detect_language
        text = Path(path).read_text(encoding="utf-8")

        # Call our deterministic language detector
        lang = detect_language(text, fallback_lang=fallback_lang)

        lines = text.strip().split("\n")

        title = ""
        sections = []
        current_section = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# ") and not title:
                title = stripped[2:].strip()
            elif stripped.startswith("## "):
                current_section = {"heading": stripped[3:].strip(), "level": "h2", "lines": []}
                sections.append(current_section)
            elif stripped.startswith("### "):
                current_section = {"heading": stripped[4:].strip(), "level": "h3", "lines": []}
                sections.append(current_section)
            elif current_section is not None and stripped:
                current_section["lines"].append(stripped)

        # Build image slots: one featured + one per h2 section
        h2_sections = [s for s in sections if s.get("level") == "h2"]
        slots = [
            {
                "slot_id": "featured",
                "purpose": "featured_image",
                "preferred_type": "landscape",
                "section_excerpt": title,
            }
        ]
        for i, sec in enumerate(h2_sections):
            excerpt = " ".join(sec.get("lines", []))[:200]
            slots.append({
                "slot_id": f"section_{i}",
                "purpose": f"inline_after_{sec['heading'].lower().replace(' ', '_')}",
                "preferred_type": "any",
                "target_heading": sec["heading"],
                "section_excerpt": excerpt.strip(),
            })

        for sec in sections:
            sec.pop("lines", None)

        return cls(
            article_title=title,
            article_language=lang,
            sections=sections,
            image_slots=slots,
            source_path=str(path),
            confidence=0.8,
        )

    @classmethod
    def from_html(
        cls,
        content: str,
        *,
        title: str = "",
        article_id: str | int | None = None,
        source_path: str | None = None,
        fallback_lang: str = "en",
    ) -> "VisualBrief":
        """Build a brief from rendered HTML or Gutenberg block content.

        WordPress stores Gutenberg blocks as HTML with block comments. The
        visual planner needs headings and nearby text, not a Markdown export,
        so this parser deliberately reads the stable HTML boundary.
        """
        from pictovap.core.language import detect_language

        class PlainTextParser(HTMLParser):
            block_tags = {
                "address", "article", "aside", "blockquote", "br", "dd", "div",
                "dl", "dt", "figcaption", "figure", "footer", "form", "h1", "h2",
                "h3", "h4", "h5", "h6", "header", "hr", "li", "main", "nav",
                "ol", "p", "pre", "section", "table", "tbody", "td", "tfoot",
                "th", "thead", "tr", "ul",
            }

            def __init__(self) -> None:
                super().__init__(convert_charrefs=True)
                self.parts: list[str] = []

            def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
                if tag in self.block_tags:
                    self.parts.append(" ")

            def handle_endtag(self, tag: str) -> None:
                if tag in self.block_tags:
                    self.parts.append(" ")

            def handle_data(self, data: str) -> None:
                self.parts.append(data)

        def plain_text(value: str) -> str:
            parser = PlainTextParser()
            parser.feed(value)
            parser.close()
            return re.sub(r"\s+", " ", "".join(parser.parts)).strip()

        heading_pattern = re.compile(r"<h(?P<level>[1-3])\b[^>]*>(?P<body>.*?)</h(?P=level)>", re.I | re.S)
        matches = list(heading_pattern.finditer(content))
        resolved_title = plain_text(title)
        if not resolved_title:
            first_h1 = next((match for match in matches if match.group("level") == "1"), None)
            resolved_title = plain_text(first_h1.group("body")) if first_h1 else "Untitled article"

        sections: list[dict[str, str]] = []
        h2_sections: list[tuple[dict[str, str], str]] = []
        for index, match in enumerate(matches):
            level = match.group("level")
            if level == "1":
                continue
            heading = plain_text(match.group("body"))
            if not heading:
                continue
            next_start = matches[index + 1].start() if index + 1 < len(matches) else len(content)
            excerpt = plain_text(content[match.end():next_start])[:200]
            section = {"heading": heading, "level": f"h{level}"}
            sections.append(section)
            if level == "2":
                h2_sections.append((section, excerpt))

        slots: list[dict[str, Any]] = [{
            "slot_id": "featured",
            "purpose": "featured_image",
            "preferred_type": "landscape",
            "section_excerpt": resolved_title,
        }]
        for index, (section, excerpt) in enumerate(h2_sections):
            slots.append({
                "slot_id": f"section_{index}",
                "purpose": f"inline_after_{section['heading'].lower().replace(' ', '_')}",
                "preferred_type": "any",
                "target_heading": section["heading"],
                "section_excerpt": excerpt,
            })

        article_text = " ".join([resolved_title, plain_text(content)])
        return cls(
            article_title=resolved_title,
            article_id=str(article_id) if article_id is not None else None,
            article_language=detect_language(article_text, fallback_lang=fallback_lang),
            topic=resolved_title,
            sections=sections,
            image_slots=slots,
            source_path=source_path,
            confidence=0.8,
        )


@dataclass
class FitScore:
    """
    A transparent scoring explanation for a candidate image against a slot.

    The scoring is rule-based and deterministic. It is not ML.
    Each dimension is scored independently; the final_score is a weighted sum.
    """
    candidate_id: str
    slot_id: str = ""
    contextual_relevance: float = 0.0
    section_relevance: float = 0.0
    technical_quality: float = 0.0
    duplication_risk: float = 0.0
    source_trust: float = 0.0
    license_confidence: float = 0.0
    cms_suitability: float = 0.0
    final_score: float = 0.0
    decision: str = "needs_review"  # selected | rejected | needs_review
    human_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "slot_id": self.slot_id,
            "contextual_relevance": self.contextual_relevance,
            "section_relevance": self.section_relevance,
            "technical_quality": self.technical_quality,
            "duplication_risk": self.duplication_risk,
            "source_trust": self.source_trust,
            "license_confidence": self.license_confidence,
            "cms_suitability": self.cms_suitability,
            "final_score": self.final_score,
            "decision": self.decision,
            "human_reason": self.human_reason,
        }


@dataclass
class ProvenancePack:
    """
    A persistent audit trail for a selected image.

    This is not a legal guarantee. It is a structured provenance record
    that tracks where an image came from, how it was processed, and
    where it was placed.
    """
    image_id: str
    source_type: str = "local"  # local | api | url
    provider: str = ""
    source_url: Optional[str] = None
    local_source_path: Optional[str] = None
    license_status: LicenseType | str | None = LicenseType.UNKNOWN

    def __post_init__(self) -> None:
        self.license_status = LicenseType.from_string(self.license_status)
    attribution: Optional[str] = None
    original_filename: str = ""
    generated_filename: str = ""
    content_hash: str = ""
    article_id: Optional[str] = None
    slot_id: str = ""
    placement_target: str = ""
    generated_alt_text: str = ""
    generated_caption: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    processing_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_id": self.image_id,
            "source_type": self.source_type,
            "provider": self.provider,
            "source_url": self.source_url,
            "local_source_path": self.local_source_path,
            "license_status": LicenseType.from_string(self.license_status).value,
            "attribution": self.attribution,
            "original_filename": self.original_filename,
            "generated_filename": self.generated_filename,
            "content_hash": self.content_hash,
            "article_id": self.article_id,
            "slot_id": self.slot_id,
            "placement_target": self.placement_target,
            "generated_alt_text": self.generated_alt_text,
            "generated_caption": self.generated_caption,
            "timestamp": self.timestamp,
            "processing_actions": self.processing_actions,
        }


@dataclass
class PlacementInstruction:
    """
    A single instruction for placing one image into the CMS.
    """
    slot_id: str
    output_path: str
    target_section: str = ""
    placement_strategy: str = "after_heading"
    image_role: str = "content"  # featured | content | gallery
    alt_text: str = ""
    caption: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlacementInstruction":
        """Rebuild one instruction from a serialized visual plan."""
        if not isinstance(data, dict):
            raise ValueError("Each CMS placement instruction must be an object")
        try:
            return cls(
                slot_id=data["slot_id"],
                output_path=data["output_path"],
                target_section=data.get("target_section", ""),
                placement_strategy=data.get("placement_strategy", "after_heading"),
                image_role=data.get("image_role", "content"),
                alt_text=data.get("alt_text", ""),
                caption=data.get("caption", ""),
            )
        except KeyError as exc:
            raise ValueError(f"CMS placement instruction is missing '{exc.args[0]}'") from exc

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "output_path": self.output_path,
            "target_section": self.target_section,
            "placement_strategy": self.placement_strategy,
            "image_role": self.image_role,
            "alt_text": self.alt_text,
            "caption": self.caption,
        }


@dataclass
class CMSPlacement:
    """
    A CMS-agnostic placement plan describing where and how
    images should be injected into the destination platform.

    WordPress/Gutenberg can implement this plan, but the model
    itself is not WordPress-specific.
    """
    article_id: str
    adapter_target: str = "mock"
    target_platform: str = "generic"
    placements: List[PlacementInstruction] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CMSPlacement":
        """Rebuild the typed CMS boundary from a JSON plan."""
        if not isinstance(data, dict):
            raise ValueError("CMS placement must be an object")
        try:
            article_id = data["article_id"]
            raw_placements = data["placements"]
        except KeyError as exc:
            raise ValueError(f"CMS placement is missing '{exc.args[0]}'") from exc
        if not isinstance(raw_placements, list):
            raise ValueError("CMS placement 'placements' must be a list")
        return cls(
            article_id=article_id,
            adapter_target=data.get("adapter_target", "mock"),
            target_platform=data.get("target_platform", "generic"),
            placements=[PlacementInstruction.from_dict(item) for item in raw_placements],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "article_id": self.article_id,
            "adapter_target": self.adapter_target,
            "target_platform": self.target_platform,
            "placements": [p.to_dict() for p in self.placements],
        }
