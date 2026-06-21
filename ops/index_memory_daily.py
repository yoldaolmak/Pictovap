#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from src.utils.config import get_visual_memory_db_path
from src.core.database import VisualMemoryComponent, VisualMemoryConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HDD/Mac Photos index + free Vision enrich")
    parser.add_argument("--mode", choices=("hdd", "photos", "hybrid"), default="hdd")
    parser.add_argument("--external-root", action="append", default=[], help="HDD kok yolu (birden fazla verilebilir)")
    parser.add_argument("--folder", default="", help="Pilot test icin tek klasor")
    parser.add_argument("--photos-library", default=str(Path("~/Pictures/Photos Library.photoslibrary").expanduser()))
    parser.add_argument("--overlay", action="store_true", help="Photos app metadata overlay")
    parser.add_argument("--daily-limit", type=int, default=8, help="Gunluk free Vision tarama limiti")
    parser.add_argument("--best-query", default="", help="Sorguya gore en iyi secim")
    parser.add_argument("--best-limit", type=int, default=2, help="En iyi secim adedi (1-2 onerilir)")
    parser.add_argument("--allow-personal", action="store_true", help="Kisisel foto filtrelemesini kapat")
    parser.add_argument("--min-quality", type=float, default=0.72, help="Min quality score (0-1)")
    parser.add_argument("--min-selection", type=float, default=0.78, help="Min selection score")
    parser.add_argument("--min-pixels", type=int, default=900000, help="Min cozumurluk pikseli")
    parser.add_argument("--batch-size", type=int, default=200, help="Ara checkpoint DB batch adedi")
    parser.add_argument("--progress-interval", type=int, default=500, help="Progress log araligi (dosya)")
    parser.add_argument("--report-sample", type=int, default=50, help="Final kalite raporu sample adedi")
    return parser.parse_args()


def _existing_dirs(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    for item in paths:
        expanded = item.expanduser()
        if expanded.exists() and expanded.is_dir():
            result.append(expanded)
    return result


def _auto_hdd_roots() -> list[Path]:
    volumes = Path("/Volumes")
    if not volumes.exists():
        return []
    roots = []
    for item in volumes.iterdir():
        name = item.name.lower()
        if not item.is_dir():
            continue
        if name in {"macintosh hd", "com.apple.timemachine.localsnapshots"}:
            continue
        roots.append(item)
    return roots


def main() -> None:
    args = parse_args()
    mode = args.mode

    scan_photos = mode in {"photos", "hybrid"}
    hdd_roots = _existing_dirs([Path(item) for item in args.external_root])
    if args.folder:
        hdd_roots = _existing_dirs([Path(args.folder)])
    if mode in {"hdd", "hybrid"} and not hdd_roots:
        hdd_roots = _auto_hdd_roots()

    if mode in {"hdd", "hybrid"} and not hdd_roots:
        print("error=no_hdd_root_found")
        return

    config = VisualMemoryConfig(
        database_path=get_visual_memory_db_path(),
        external_roots=hdd_roots,
        photos_library_path=Path(args.photos_library).expanduser(),
        scan_photos_library=scan_photos,
        load_photos_app_overlay=args.overlay,
        daily_vision_scan_limit=args.daily_limit,
        exclude_personal_photos=not args.allow_personal,
        min_quality_score=args.min_quality,
        min_selection_score=args.min_selection,
        min_pixels=args.min_pixels,
        rebuild_batch_size=max(20, args.batch_size),
        progress_log_interval=max(50, args.progress_interval),
    )
    component = VisualMemoryComponent(config)
    print(f"mode={mode}")
    print(f"hdd_roots={[str(p) for p in hdd_roots]}")
    print(f"scan_photos={scan_photos}")
    print(f"daily_limit={args.daily_limit}")
    print(f"exclude_personal={config.exclude_personal_photos}")
    print(f"min_quality={config.min_quality_score}")
    print(f"min_selection={config.min_selection_score}")
    print(f"min_pixels={config.min_pixels}")
    print(f"batch_size={config.rebuild_batch_size}")
    print(f"progress_interval={config.progress_log_interval}")

    indexed = component.rebuild_index()
    stats = getattr(component.indexer, "last_rebuild_stats", {})
    if stats:
        print(
            "stats="
            f"discovered:{stats.get('discovered', 0)} "
            f"analyzed:{stats.get('analyzed', 0)} "
            f"kept:{stats.get('kept', indexed)} "
            f"dropped:{stats.get('dropped', 0)}"
        )
    print(f"indexed={indexed}")
    report = component.quality_report(
        sample_size=max(5, args.report_sample),
        min_quality_score=config.min_quality_score,
        min_selection_score=config.min_selection_score,
    )
    print(
        "quality_report="
        f"total:{report['total']} "
        f"personal_marked:{report['personal_marked']} "
        f"missing_location:{report['missing_location']} "
        f"low_score_rows:{report['low_score_rows']}"
    )

    best = component.pick_best_assets(
        args.best_query or None,
        limit=args.best_limit,
        source_types=("external_hdd", "mac_photos"),
    )
    if not best:
        print("best=none")
        return

    print("best:")
    for row in best:
        print(
            f"- {row['filename']} | source={row['source_type']} | "
            f"score={row['selection_score']:.3f} | personal={row['is_personal']} | "
            f"location={row['location'] or row['city'] or row['country'] or 'unknown'}"
        )


if __name__ == "__main__":
    main()
