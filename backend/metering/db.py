from __future__ import annotations
import sqlite3
from typing import Any


class MeteringDB:
    def __init__(self, path: str) -> None:
        self.path = path
        self.con = sqlite3.connect(path, check_same_thread=False)
        self.con.row_factory = sqlite3.Row

    def init(self) -> None:
        self.con.executescript("""
            CREATE TABLE IF NOT EXISTS usage_events (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                tool                TEXT    NOT NULL,
                ts                  INTEGER NOT NULL,
                model               TEXT,
                project             TEXT,
                session_id          TEXT,
                input_tokens        INTEGER DEFAULT 0,
                output_tokens       INTEGER DEFAULT 0,
                cache_read_tokens   INTEGER DEFAULT 0,
                cache_write_tokens  INTEGER DEFAULT 0,
                cost_usd            REAL    DEFAULT 0.0,
                UNIQUE(tool, session_id, ts)
            );
            CREATE TABLE IF NOT EXISTS scan_state (
                tool            TEXT    PRIMARY KEY,
                last_scan_at    INTEGER,
                last_file       TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_usage_ts
                ON usage_events(ts);
            CREATE INDEX IF NOT EXISTS idx_usage_tool
                ON usage_events(tool, ts);
        """)
        self.con.commit()

    def insert_event(
        self, tool: str, ts: int, model: str | None, project: str | None,
        session_id: str | None, input_tokens: int, output_tokens: int,
        cache_read_tokens: int, cache_write_tokens: int, cost_usd: float,
    ) -> None:
        self.con.execute(
            """INSERT OR IGNORE INTO usage_events
               (tool, ts, model, session_id, project,
                input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, cost_usd)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (tool, ts, model, session_id, project,
             input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, cost_usd),
        )
        self.con.commit()

    def set_scan_state(self, tool: str, last_scan_at: int, last_file: str) -> None:
        self.con.execute(
            "INSERT OR REPLACE INTO scan_state (tool, last_scan_at, last_file) VALUES (?,?,?)",
            (tool, last_scan_at, last_file),
        )
        self.con.commit()

    def get_scan_state(self, tool: str) -> dict[str, Any] | None:
        row = self.con.execute(
            "SELECT last_scan_at, last_file FROM scan_state WHERE tool=?", (tool,)
        ).fetchone()
        if row is None:
            return None
        return {"last_scan_at": row["last_scan_at"], "last_file": row["last_file"]}

    def query_window(self, tool: str, since_ts: int) -> list[dict[str, Any]]:
        rows = self.con.execute(
            "SELECT * FROM usage_events WHERE tool=? AND ts>=? ORDER BY ts",
            (tool, since_ts),
        ).fetchall()
        return [dict(r) for r in rows]

    def query_range(self, tool: str, since_ts: int, until_ts: int) -> list[dict[str, Any]]:
        rows = self.con.execute(
            "SELECT * FROM usage_events WHERE tool=? AND ts>=? AND ts<? ORDER BY ts",
            (tool, since_ts, until_ts),
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.con.close()
