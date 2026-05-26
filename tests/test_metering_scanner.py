import json
import pytest
import asyncio
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from metering.scanner import parse_claude_code_jsonl, parse_codex_jsonl, fetch_antigravity_ls


# ── Claude Code ──────────────────────────────────────────────

def test_parse_claude_code_assistant_entry(tmp_path):
    entry = {
        "type": "assistant",
        "timestamp": "2026-05-25T10:00:00.000Z",
        "message": {
            "model": "claude-opus-4-7",
            "usage": {
                "input_tokens": 1000,
                "output_tokens": 500,
                "cache_creation_input_tokens": 200,
                "cache_read_input_tokens": 800,
            },
        },
        "costUSD": 0.075,
    }
    f = tmp_path / "session.jsonl"
    f.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    events = parse_claude_code_jsonl(str(f), project="myproject")
    assert len(events) == 1
    e = events[0]
    assert e["tool"] == "claude_code"
    assert e["model"] == "claude-opus-4-7"
    assert e["input_tokens"] == 1000
    assert e["output_tokens"] == 500
    assert e["cache_write_tokens"] == 200
    assert e["cache_read_tokens"] == 800
    assert abs(e["cost_usd"] - 0.075) < 1e-9
    assert e["session_id"] == "session.jsonl"
    assert e["project"] == "myproject"


def test_parse_claude_code_skips_non_assistant(tmp_path):
    entries = [
        {"type": "user", "timestamp": "2026-05-25T10:00:00.000Z", "message": {"content": "hi"}},
        {"type": "assistant", "timestamp": "2026-05-25T10:01:00.000Z",
         "message": {"model": "claude-opus-4-7",
                     "usage": {"input_tokens": 100, "output_tokens": 50,
                               "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}},
         "costUSD": 0.001},
    ]
    f = tmp_path / "s.jsonl"
    f.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    events = parse_claude_code_jsonl(str(f), project="p")
    assert len(events) == 1


def test_parse_claude_code_missing_cost_defaults_zero(tmp_path):
    entry = {
        "type": "assistant",
        "timestamp": "2026-05-25T10:00:00.000Z",
        "message": {"model": "claude-haiku-4-5",
                    "usage": {"input_tokens": 50, "output_tokens": 20,
                              "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}},
    }
    f = tmp_path / "s.jsonl"
    f.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    events = parse_claude_code_jsonl(str(f), project="p")
    assert events[0]["cost_usd"] == 0.0


def test_parse_claude_code_explicit_zero_cost_preserved(tmp_path):
    entry = {
        "type": "assistant",
        "timestamp": "2026-05-25T10:00:00.000Z",
        "message": {"model": "claude-opus-4-7",
                    "usage": {"input_tokens": 1000, "output_tokens": 500,
                              "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}},
        "costUSD": 0.0,
    }
    f = tmp_path / "s.jsonl"
    f.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    events = parse_claude_code_jsonl(str(f), project="p")
    assert events[0]["cost_usd"] == 0.0


def test_parse_claude_code_malformed_line_skipped(tmp_path):
    f = tmp_path / "s.jsonl"
    f.write_text("not json\n", encoding="utf-8")
    events = parse_claude_code_jsonl(str(f), project="p")
    assert events == []


# ── Codex ────────────────────────────────────────────────────

def test_parse_codex_assistant_entry(tmp_path):
    entry = {
        "type": "message",
        "role": "assistant",
        "model": "gpt-4o",
        "timestamp": "2026-05-25T11:00:00.000Z",
        "usage": {"prompt_tokens": 300, "completion_tokens": 150},
        "cost": 0.002,
    }
    f = tmp_path / "sess.jsonl"
    f.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    events = parse_codex_jsonl(str(f), project="codex-proj")
    assert len(events) == 1
    e = events[0]
    assert e["tool"] == "codex"
    assert e["input_tokens"] == 300
    assert e["output_tokens"] == 150
    assert abs(e["cost_usd"] - 0.002) < 1e-9


def test_parse_codex_skips_user_role(tmp_path):
    entries = [
        {"type": "message", "role": "user", "model": "gpt-4o",
         "timestamp": "2026-05-25T11:00:00.000Z",
         "usage": {"prompt_tokens": 100, "completion_tokens": 0}, "cost": 0.0},
        {"type": "message", "role": "assistant", "model": "gpt-4o",
         "timestamp": "2026-05-25T11:01:00.000Z",
         "usage": {"prompt_tokens": 200, "completion_tokens": 100}, "cost": 0.001},
    ]
    f = tmp_path / "s.jsonl"
    f.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    events = parse_codex_jsonl(str(f), project="p")
    assert len(events) == 1


# ── Antigravity LS ───────────────────────────────────────────

async def test_fetch_antigravity_ls_offline():
    result = await fetch_antigravity_ls(port=19999, timeout=0.1)
    assert result["status"] == "offline"


async def test_fetch_antigravity_ls_bad_port_zero():
    result = await fetch_antigravity_ls(port=0, timeout=0.1)
    assert result["status"] == "offline"
