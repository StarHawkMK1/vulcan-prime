from __future__ import annotations
import time
from datetime import datetime, timezone, timedelta
from typing import Any

from metering.db import MeteringDB


def week_start(now: int) -> int:
    """Return unix ts of Monday 00:00 UTC for the week containing `now`."""
    dt = datetime.fromtimestamp(now, tz=timezone.utc)
    monday = dt - timedelta(days=dt.weekday())
    return int(monday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())


def today_start(now: int) -> int:
    """Return unix ts of 00:00 UTC today."""
    dt = datetime.fromtimestamp(now, tz=timezone.utc)
    return int(dt.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())


def get_window_5h(
    tool: str, db: MeteringDB, now: int, limit: int
) -> dict[str, Any]:
    since = now - 18000  # 5 hours = 18000 seconds
    rows = db.query_window(tool, since_ts=since)
    if not rows:
        return {"tokens": 0, "limit": limit, "resets_in_sec": None}
    tokens = sum(r["input_tokens"] + r["output_tokens"] for r in rows)
    oldest_ts = min(r["ts"] for r in rows)
    resets_in_sec = max(0, (oldest_ts + 18000) - now)
    return {"tokens": tokens, "limit": limit, "resets_in_sec": resets_in_sec}


def get_weekly(
    tool: str, db: MeteringDB, week_start_ts: int, limit: int
) -> dict[str, Any]:
    week_end = week_start_ts + 7 * 86400
    rows = db.query_range(tool, since_ts=week_start_ts, until_ts=week_end)
    tokens = sum(r["input_tokens"] + r["output_tokens"] for r in rows)
    cost   = sum(r["cost_usd"] for r in rows)
    return {"tokens": tokens, "limit": limit, "cost_usd": round(cost, 6)}


def get_today(
    tool: str, db: MeteringDB, today_start_ts: int
) -> dict[str, Any]:
    tomorrow = today_start_ts + 86400
    rows = db.query_range(tool, since_ts=today_start_ts, until_ts=tomorrow)
    tokens   = sum(r["input_tokens"] + r["output_tokens"] for r in rows)
    cost     = sum(r["cost_usd"] for r in rows)
    sessions = len({r["session_id"] for r in rows})
    return {"tokens": tokens, "cost_usd": round(cost, 6), "sessions": sessions}


def get_trend_7d(
    tools: list[str], db: MeteringDB, now: int
) -> list[dict[str, Any]]:
    day0 = today_start(now)
    result: list[dict[str, Any]] = []
    for i in range(6, -1, -1):
        day_start_ts = day0 - i * 86400
        day_end_ts   = day_start_ts + 86400
        dt_str       = datetime.fromtimestamp(day_start_ts, tz=timezone.utc).strftime("%Y-%m-%d")
        entry: dict[str, Any] = {"date": dt_str, "cost_usd": 0.0}
        for tool in tools:
            rows = db.query_range(tool, since_ts=day_start_ts, until_ts=day_end_ts)
            tok  = sum(r["input_tokens"] + r["output_tokens"] for r in rows)
            cost = sum(r["cost_usd"] for r in rows)
            entry[tool] = tok
            entry["cost_usd"] = round(entry["cost_usd"] + cost, 6)
        result.append(entry)
    return result


def build_dashboard_payload(
    db: MeteringDB,
    now: int,
    week_start_ts: int,
    today_start_ts: int,
    limits: dict[str, int],
    ag_status: str,
    ag_last_seen: str | None,
) -> dict[str, Any]:
    tools: dict[str, Any] = {}

    tools["claude_code"] = {
        "status": "live",
        "window_5h": get_window_5h("claude_code", db, now, limits["cc_5h"]),
        "weekly":    get_weekly("claude_code", db, week_start_ts, limits["cc_weekly"]),
        "today":     get_today("claude_code", db, today_start_ts),
    }

    tools["codex"] = {
        "status": "live",
        "window_5h": get_window_5h("codex", db, now, limits["codex_5h"]),
        "weekly":    get_weekly("codex", db, week_start_ts, limits["codex_weekly"]),
        "today":     get_today("codex", db, today_start_ts),
    }

    tools["antigravity"] = {
        "status": ag_status,
        "last_seen": ag_last_seen,
        "window_5h": get_window_5h("antigravity", db, now, limits["ag_5h"])
                     if ag_status == "live" else
                     {"tokens": None, "limit": limits["ag_5h"], "resets_in_sec": None},
        "weekly":    get_weekly("antigravity", db, week_start_ts, limits["ag_weekly"]),
        "today":     get_today("antigravity", db, today_start_ts)
                     if ag_status == "live" else
                     {"tokens": None, "cost_usd": None, "sessions": None},
    }

    trend    = get_trend_7d(["claude_code", "codex", "antigravity"], db, now)
    wk_rows  = db.query_range("claude_code", week_start_ts, week_start_ts + 7 * 86400)
    wk_rows += db.query_range("codex",       week_start_ts, week_start_ts + 7 * 86400)
    wk_rows += db.query_range("antigravity", week_start_ts, week_start_ts + 7 * 86400)
    wk_tokens = sum(r["input_tokens"] + r["output_tokens"] for r in wk_rows)
    wk_cost   = round(sum(r["cost_usd"] for r in wk_rows), 6)

    return {
        "scanned_at":   datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
        "tools":        tools,
        "trend_7d":     trend,
        "weekly_total": {"tokens": wk_tokens, "cost_usd": wk_cost},
    }
