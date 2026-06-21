#!/usr/bin/env python3
"""
yo_vision_daily_scan.py — Günlük Google Cloud Vision taraması
Kota: Aylık free tier'ın %80'i = 800 unit (hard cap).
Cron ile her gün 09:00'da çalışır.
"""
from __future__ import annotations

import calendar
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.core.settings import get_visual_memory_db_path, load_project_env

load_project_env()

from scripts.vision_budget import _load_state, _month, _today
from src.visual_memory.db import VisualMemoryDatabase
from src.core.yo_cloud_vision import YOCloudVisionClient

# ── Bütçe sabitleri ─────────────────────────────────────────────────────────
MONTHLY_FREE_UNITS = 1000
MONTHLY_BUDGET_CAP = int(MONTHLY_FREE_UNITS * 0.80)   # 800 unit — asla geçme
MAX_DAILY_LIMIT    = 26                                 # 800/31 ≈ 26 (güvenli üst sınır)
LOG_PREFIX = "[vision-scan]"


def _days_remaining_in_month() -> int:
    now = datetime.now()
    last_day = calendar.monthrange(now.year, now.month)[1]
    return max(1, last_day - now.day + 1)  # bugün dahil


def calculate_daily_limit() -> tuple[int, int, int]:
    """(bugün_limit, ay_kullanılan, ay_kalan) döndürür."""
    state      = _load_state()
    month_used = int(state.get("monthly", {}).get(_month(), 0))
    today_used = int(state.get("daily",   {}).get(_today(), 0))

    remaining_monthly = max(0, MONTHLY_BUDGET_CAP - month_used)
    days_left         = _days_remaining_in_month()

    # Kalan kotayı kalan günlere eşit dağıt, MAX_DAILY_LIMIT ile kır
    daily_pace    = remaining_monthly // days_left
    safe_daily    = min(MAX_DAILY_LIMIT, daily_pace)
    today_remaining = max(0, safe_daily - today_used)

    return today_remaining, month_used, remaining_monthly


def main() -> None:
    limit, month_used, month_remaining = calculate_daily_limit()

    print(
        f"{LOG_PREFIX} month={month_used}/{MONTHLY_BUDGET_CAP} "
        f"remaining={month_remaining} today_limit={limit}"
    )

    if limit <= 0:
        print(f"{LOG_PREFIX} kota doldu veya günlük limit aşıldı — atlanıyor")
        return

    db_path = get_visual_memory_db_path()
    if not db_path.exists():
        print(f"{LOG_PREFIX} DB bulunamadı: {db_path}")
        return

    db   = VisualMemoryDatabase(db_path)
    rows = db.pending_vision_candidates(limit=limit)

    if not rows:
        print(f"{LOG_PREFIX} bekleyen aday yok (limit={limit})")
        return

    print(f"{LOG_PREFIX} {len(rows)} görsel taranacak")

    try:
        client = YOCloudVisionClient()
    except Exception as e:
        print(f"{LOG_PREFIX} GCV başlatılamadı: {e}")
        return

    scanned_at = datetime.now().isoformat(timespec="seconds")
    done = 0
    errors = 0

    for row in rows:
        path = row["source_path"]

        if not Path(path).exists():
            db.update_vision_result(
                row["source_id"], {}, scanned_at=scanned_at, error="file_not_found"
            )
            errors += 1
            print(f"  ✗ {Path(path).name}: dosya bulunamadı")
            continue

        # Kota kontrolü — her adımda yeniden kontrol et (başka process tüketmiş olabilir)
        remaining, mu, _ = calculate_daily_limit()
        if remaining <= 0:
            print(f"{LOG_PREFIX} günlük kota doldu, duruyorum (month={mu}/{MONTHLY_BUDGET_CAP})")
            break

        result = client.analyze(path)

        if result.get("success"):
            db.update_vision_result(row["source_id"], result, scanned_at=scanned_at)
            done += 1
            labels_preview = ", ".join(
                (item.get("description", "") if isinstance(item, dict) else str(item))
                for item in result.get("labels", [])[:3]
            )
            print(f"  ✓ {Path(path).name}: {labels_preview}")
        else:
            err_msg = str(result.get("error", "unknown"))[:120]
            db.update_vision_result(
                row["source_id"], {}, scanned_at=scanned_at, error=err_msg
            )
            errors += 1
            print(f"  ✗ {Path(path).name}: {err_msg}")

    # Final durum
    final_state = _load_state()
    final_month  = int(final_state.get("monthly", {}).get(_month(), 0))
    final_today  = int(final_state.get("daily",   {}).get(_today(), 0))
    print(
        f"{LOG_PREFIX} bitti: done={done} errors={errors} "
        f"today={final_today} month={final_month}/{MONTHLY_BUDGET_CAP}"
    )

    # Hard cap uyarısı
    if final_month >= MONTHLY_BUDGET_CAP:
        print(f"{LOG_PREFIX} ⚠️  AYLIK KOTA DOLDU ({MONTHLY_BUDGET_CAP}) — ay sonuna kadar tarama yok")


if __name__ == "__main__":
    main()
