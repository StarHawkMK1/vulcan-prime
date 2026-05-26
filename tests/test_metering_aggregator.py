import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from metering.db import MeteringDB
from metering.aggregator import (
    get_window_5h, get_weekly, get_today, get_trend_7d,
    build_dashboard_payload,
)


@pytest.fixture
def db(tmp_path):
    d = MeteringDB(str(tmp_path / "agg.db"))
    d.init()
    return d


# Frozen "now" = 1700100000 (Mon 2023-11-16 00:00:00 UTC happens to work)
# Week starts Mon 2023-11-13 00:00:00 UTC = 1699833600
NOW = 1700100000
WEEK_START = 1699833600   # Monday 00:00 UTC of the week containing NOW
TODAY_START = NOW - (NOW % 86400)  # start of UTC day containing NOW


def _ins(db, tool, ts, tok_in, tok_out, cost, sid="s1"):
    db.insert_event(tool, ts, "claude-opus-4-7", "proj", sid,
                    tok_in, tok_out, 0, 0, cost)


def test_window_5h_counts_only_recent(db):
    _ins(db, "claude_code", NOW - 1000, 500, 200, 0.01, "s1")
    _ins(db, "claude_code", NOW - 20000, 1000, 400, 0.02, "s2")  # outside 5H
    result = get_window_5h("claude_code", db, now=NOW, limit=500000)
    assert result["tokens"] == 700
    assert result["resets_in_sec"] > 0
    assert result["limit"] == 500000


def test_window_5h_resets_in_sec(db):
    oldest_ts = NOW - 10000
    _ins(db, "codex", oldest_ts, 100, 50, 0.001, "s1")
    result = get_window_5h("codex", db, now=NOW, limit=0)
    expected_reset = (oldest_ts + 18000) - NOW
    assert abs(result["resets_in_sec"] - expected_reset) <= 1


def test_window_5h_empty(db):
    result = get_window_5h("claude_code", db, now=NOW, limit=500000)
    assert result["tokens"] == 0
    assert result["resets_in_sec"] is None


def test_weekly_sums_week(db):
    _ins(db, "claude_code", WEEK_START + 100, 1000, 400, 0.05, "w1")
    _ins(db, "claude_code", WEEK_START + 200, 500, 200, 0.02, "w2")
    _ins(db, "claude_code", WEEK_START - 1, 9999, 9999, 9.99, "old")  # before week
    result = get_weekly("claude_code", db, week_start_ts=WEEK_START, limit=5000000)
    assert result["tokens"] == 2100
    assert abs(result["cost_usd"] - 0.07) < 1e-9
    assert result["limit"] == 5000000


def test_today_sums_today(db):
    _ins(db, "codex", TODAY_START + 100, 300, 100, 0.003, "t1")
    _ins(db, "codex", TODAY_START - 1, 999, 999, 0.999, "yday")
    result = get_today("codex", db, today_start_ts=TODAY_START)
    assert result["tokens"] == 400
    assert result["sessions"] == 1


def test_trend_7d_returns_7_entries(db):
    trend = get_trend_7d(["claude_code", "codex", "antigravity"], db, now=NOW)
    assert len(trend) == 7
    for entry in trend:
        assert "date" in entry
        assert "claude_code" in entry
        assert "codex" in entry
        assert "antigravity" in entry
        assert "cost_usd" in entry


def test_build_dashboard_payload_shape(db):
    _ins(db, "claude_code", NOW - 500, 200, 100, 0.005, "x1")
    payload = build_dashboard_payload(
        db=db, now=NOW,
        week_start_ts=WEEK_START, today_start_ts=TODAY_START,
        limits={
            "cc_5h": 500000, "cc_weekly": 5000000,
            "codex_5h": 500000, "codex_weekly": 5000000,
            "ag_5h": 0, "ag_weekly": 0,
        },
        ag_status="offline", ag_last_seen=None,
    )
    assert "tools" in payload
    assert "trend_7d" in payload
    assert "weekly_total" in payload
    assert payload["tools"]["claude_code"]["status"] == "live"
    assert payload["tools"]["antigravity"]["status"] == "offline"
