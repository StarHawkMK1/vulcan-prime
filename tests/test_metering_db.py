import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from metering.db import MeteringDB


@pytest.fixture
def db(tmp_path):
    d = MeteringDB(str(tmp_path / "test.db"))
    d.init()
    return d


def test_init_creates_tables(db):
    rows = db.con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    names = {r[0] for r in rows}
    assert "usage_events" in names
    assert "scan_state" in names


def test_insert_event(db):
    db.insert_event(
        tool="claude_code", ts=1700000000, model="claude-opus-4-7",
        project="myproject", session_id="abc.jsonl",
        input_tokens=100, output_tokens=50,
        cache_read_tokens=200, cache_write_tokens=10,
        cost_usd=0.005,
    )
    row = db.con.execute("SELECT * FROM usage_events").fetchone()
    assert row is not None
    assert row[1] == "claude_code"
    assert row["session_id"] == "abc.jsonl"


def test_duplicate_insert_ignored(db):
    for _ in range(3):
        db.insert_event(
            tool="claude_code", ts=1700000000, model="claude-opus-4-7",
            project="p", session_id="abc.jsonl",
            input_tokens=100, output_tokens=50,
            cache_read_tokens=0, cache_write_tokens=0, cost_usd=0.001,
        )
    count = db.con.execute("SELECT COUNT(*) FROM usage_events").fetchone()[0]
    assert count == 1


def test_scan_state_round_trip(db):
    db.set_scan_state("claude_code", last_scan_at=1700000000, last_file="f.jsonl")
    state = db.get_scan_state("claude_code")
    assert state["last_scan_at"] == 1700000000
    assert state["last_file"] == "f.jsonl"


def test_scan_state_missing_returns_none(db):
    assert db.get_scan_state("codex") is None


def test_query_window(db):
    now = 1700010000
    # inside 5H window (18000 seconds)
    db.insert_event("claude_code", now - 1000, "claude-opus-4-7", "p", "s1",
                    500, 200, 0, 0, 0.01)
    # outside 5H window
    db.insert_event("claude_code", now - 20000, "claude-opus-4-7", "p", "s2",
                    1000, 400, 0, 0, 0.02)
    rows = db.query_window("claude_code", since_ts=now - 18000)
    assert len(rows) == 1
    assert rows[0]["session_id"] == "s1"


def test_query_range(db):
    db.insert_event("claude_code", 1700000100, "m", "p", "s1", 100, 50, 0, 0, 0.01)
    db.insert_event("claude_code", 1700000200, "m", "p", "s2", 200, 100, 0, 0, 0.02)
    db.insert_event("claude_code", 1700000400, "m", "p", "s3", 300, 150, 0, 0, 0.03)
    rows = db.query_range("claude_code", since_ts=1700000100, until_ts=1700000400)
    assert len(rows) == 2  # s3 at ts=400 is excluded (half-open interval)
    assert rows[0]["session_id"] == "s1"
    assert rows[1]["session_id"] == "s2"
