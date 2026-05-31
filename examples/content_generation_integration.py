from pathlib import Path

from visual_memory import VisualMemoryComponent, VisualMemoryConfig


def build_asset_index() -> None:
    component = VisualMemoryComponent(
        VisualMemoryConfig(
            database_path=Path("~/Library/Application Support/YO_OS_VIL/visual_memory.db").expanduser(),
            external_roots=[Path("/Volumes/ExternalHDD")],
        )
    )
    total = component.rebuild_index()
    print(f"indexed: {total}")


def build_article_visual_plan(article_html: str) -> None:
    component = VisualMemoryComponent(
        VisualMemoryConfig(
            database_path=Path("~/Library/Application Support/YO_OS_VIL/visual_memory.db").expanduser(),
        )
    )
    plan = component.plan_article_visuals(article_html, candidates_per_slot=3, source_types=("mac_photos",))
    for recommendation in plan.recommendations:
        print(f"{recommendation.slot.heading} [{recommendation.slot.slot_type}]")
        for candidate in recommendation.candidates:
            print(f"  - {candidate.source_path} ({candidate.reason})")


def search_assets(query: str) -> None:
    component = VisualMemoryComponent(
        VisualMemoryConfig(
            database_path=Path("~/Library/Application Support/YO_OS_VIL/visual_memory.db").expanduser(),
        )
    )
    for row in component.search_assets(query, limit=10):
        print(f"{row['source_path']} | {row['scene']} | {row['activity']} | {row['quality_score']}")
