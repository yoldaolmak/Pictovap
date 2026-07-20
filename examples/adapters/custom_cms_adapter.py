#!/usr/bin/env python3
"""Runnable skeleton for a custom CMS adapter, end to end.

A CMS adapter consumes Pictovap's CMS-agnostic placement plan
(`pictovap.core.primitives.CMSPlacement`) and executes it against a real
platform. The contract is `pictovap.core.adapters.CMSAdapter`: implement
`place(placement)` and return a dict with `placed`, `failed`, `warnings`.

This example "publishes" to a folder of Markdown files — a stand-in for a
static site generator — and demonstrates the full pipeline without any
credentials or network access:

1. Run the real planner (`create_visual_plan`) on the packaged sample
   article.
2. Rebuild the `CMSPlacement` from the plan output.
3. Hand it to the custom adapter, which writes the result to disk.

Run it:

    python examples/adapters/custom_cms_adapter.py

It writes `published/sample-article.md` under the current directory.

See docs/contributing/adapters.md for the checklist to ship a real one in
`src/pictovap/publishers/` (Ghost and Strapi are reference
implementations of API-backed adapters).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from pictovap.core.adapters import CMSAdapter
from pictovap.core.primitives import CMSPlacement, PlacementInstruction
from pictovap import create_visual_plan


class MarkdownFolderAdapter:
    """Places images by writing a Markdown document into an output folder.

    A real adapter would talk to a CMS API here (see
    `pictovap.services.wordpress.WordPressUploader.place` for the most
    complete example). The shape of `place()` — consume instructions,
    report placed/failed/warnings, never raise for a single bad
    instruction — is what carries over.
    """

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)

    def place(self, placement: CMSPlacement) -> Dict[str, Any]:
        placed, failed, warnings = [], [], []
        lines = [f"# Published: {placement.article_id}", ""]

        for instruction in placement.placements:
            if not instruction.output_path:
                failed.append({"slot_id": instruction.slot_id, "error": "no output_path"})
                continue
            if not instruction.alt_text:
                warnings.append(f"{instruction.slot_id}: empty alt text hurts accessibility")

            lines.append(f"## {instruction.target_section or '(document top)'}")
            lines.append(f"![{instruction.alt_text}]({instruction.output_path})")
            if instruction.caption:
                lines.append(f"*{instruction.caption}*")
            lines.append("")
            placed.append({"slot_id": instruction.slot_id, "role": instruction.image_role})

        self.output_dir.mkdir(parents=True, exist_ok=True)
        target = self.output_dir / f"{placement.article_id}.md"
        target.write_text("\n".join(lines), encoding="utf-8")

        return {"placed": placed, "failed": failed, "warnings": warnings, "file": str(target)}


def placement_from_plan(plan: Dict[str, Any]) -> CMSPlacement:
    """Rebuild the CMSPlacement primitive from a plan's JSON shape."""
    placement_data = plan["cms_placement"]
    return CMSPlacement(
        article_id=placement_data["article_id"],
        adapter_target="markdown-folder-example",
        target_platform="static-markdown",
        placements=[
            PlacementInstruction(
                slot_id=item["slot_id"],
                output_path=item["output_path"],
                target_section=item.get("target_section", ""),
                placement_strategy=item.get("placement_strategy", "after_heading"),
                image_role=item.get("image_role", "content"),
                alt_text=item.get("alt_text", ""),
                caption=item.get("caption", ""),
            )
            for item in placement_data["placements"]
        ],
    )


def main() -> None:
    from importlib.resources import as_file, files

    sample_resource = files("pictovap.data").joinpath("sample-article.md")
    with as_file(sample_resource) as sample:
        plan = create_visual_plan(str(sample))
    placement = placement_from_plan(plan)

    adapter = MarkdownFolderAdapter(output_dir="published")
    assert isinstance(adapter, CMSAdapter)
    print("contract check: MarkdownFolderAdapter satisfies CMSAdapter")

    result = adapter.place(placement)
    print(f"placed: {len(result['placed'])}, failed: {len(result['failed'])}, "
          f"warnings: {len(result['warnings'])}")
    print(f"output: {result['file']}")


if __name__ == "__main__":
    main()
