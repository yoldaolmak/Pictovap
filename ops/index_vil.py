#!/usr/bin/env python3
from __future__ import annotations

import argparse

from src.utils.config import get_vil_dir, get_visual_memory_db_path, load_project_env
from src.core.database import VisualMemoryComponent, VisualMemoryConfig


load_project_env()


def build_component() -> VisualMemoryComponent:
    vil_dir = get_vil_dir()
    db_path = get_visual_memory_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return VisualMemoryComponent(
        VisualMemoryConfig(
            database_path=db_path,
            external_roots=[vil_dir],
            scan_photos_library=False,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Index YO VIL assets into visual_memory.db")
    parser.add_argument("--list", action="store_true", help="show recent indexed assets after rebuild")
    parser.add_argument("--limit", type=int, default=10, help="recent asset count for --list")
    args = parser.parse_args()

    component = build_component()
    total = component.rebuild_index()
    print(f"indexed={total}")
    print(f"vil_dir={get_vil_dir()}")
    print(f"db={get_visual_memory_db_path()}")

    if not args.list:
        return

    rows = component.list_assets(limit=args.limit, source_root=get_vil_dir(), source_types=("external_hdd",))
    for row in rows:
        print(f"{row['filename']} | {row['source_path']} | {row['quality_score']}")


if __name__ == "__main__":
    main()
