#!/usr/bin/env python3
import csv
import subprocess
from pathlib import Path


ROOT = Path("/root/YO_OS_VIL/YO_OS_VIL")
INPUT_DIR = Path("/root/tmp/CMA Urun")
OUTPUT_DIR = ROOT / "exports" / "cma_urun_800"
MANIFEST = ROOT / "cma_batch_manifest.csv"
SCRIPT = ROOT / "cma_square_export.py"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    for row in rows:
        cmd = [
            "python3",
            str(SCRIPT),
            "--input",
            str(INPUT_DIR / row["source_file"]),
            "--output-dir",
            str(OUTPUT_DIR),
            "--output-name",
            row["output_name"],
            "--product",
            row["product"],
            "--form",
            row["form"],
            "--animal",
            row["animal"],
            "--weight",
            row["weight"],
        ]
        subprocess.check_call(cmd)

    print(f"exported={len(rows)}")
    print(f"output_dir={OUTPUT_DIR}")


if __name__ == "__main__":
    main()
