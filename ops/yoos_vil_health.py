#!/usr/bin/env python3
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

from src.utils.config import get_vil_dir, get_visual_memory_db_path, load_project_env

load_project_env()
ROOT = Path(__file__).resolve().parent
REQUIRED = ["PIL", "anthropic", "requests", "numpy", "cv2"]

print(f"root={ROOT}")
print(f"python={sys.executable}")
print(f"python_version={sys.version.split()[0]}")
print(f"vil_dir={get_vil_dir()}")
print(f"visual_memory_db={get_visual_memory_db_path()}")
print(f"env_file={(ROOT / '.env').exists()}")
print(f"anthropic_key={'set' if os.environ.get('ANTHROPIC_API_KEY') else 'missing'}")

failed = False
for name in REQUIRED:
    try:
        importlib.import_module(name)
        print(f"module:{name}=ok")
    except Exception as exc:
        failed = True
        print(f"module:{name}=fail:{exc}")

if failed:
    raise SystemExit(1)
print("status=ok")
