from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


STATE_PATH = Path(__file__).resolve().parent / "data" / "vision_usage.json"


@dataclass(slots=True)
class VisionBudgetStatus:
    allowed: bool
    today_count: int
    daily_limit: int
    month_units: int
    monthly_limit: int


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _month() -> str:
    return datetime.now().strftime("%Y-%m")


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {"daily": {}, "monthly": {}}
    try:
        return json.loads(STATE_PATH.read_text())
    except json.JSONDecodeError:
        return {"daily": {}, "monthly": {}}


def _save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=True, indent=2) + "\n")


def check_budget(*, units_per_image: int, daily_limit: int, monthly_limit: int) -> VisionBudgetStatus:
    state = _load_state()
    today_count = int(state.get("daily", {}).get(_today(), 0))
    month_units = int(state.get("monthly", {}).get(_month(), 0))
    allowed = today_count < daily_limit and (month_units + units_per_image) <= monthly_limit
    return VisionBudgetStatus(
        allowed=allowed,
        today_count=today_count,
        daily_limit=daily_limit,
        month_units=month_units,
        monthly_limit=monthly_limit,
    )


def consume_budget(*, units_per_image: int) -> None:
    state = _load_state()
    daily = state.setdefault("daily", {})
    monthly = state.setdefault("monthly", {})
    daily[_today()] = int(daily.get(_today(), 0)) + 1
    monthly[_month()] = int(monthly.get(_month(), 0)) + units_per_image
    _save_state(state)
