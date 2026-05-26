from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import aiohttp
    _AIOHTTP = True
except ImportError:
    _AIOHTTP = False


# ── Pricing table (per million tokens, USD) ──────────────────
_PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4-7":   {"input": 15.0,  "output": 75.0},
    "claude-sonnet-4-6": {"input": 3.0,   "output": 15.0},
    "gpt-4o":            {"input": 2.5,   "output": 10.0},
    "gpt-4o-mini":       {"input": 0.15,  "output": 0.6},
    "o3":                {"input": 10.0,  "output": 40.0},
    "o4-mini":           {"input": 1.1,   "output": 4.4},
}


def _calc_cost(model: str | None, input_tokens: int, output_tokens: int) -> float:
    p = _PRICING.get(model or "", {"input": 0.0, "output": 0.0})
    return (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000


def _parse_ts(ts_str: str | None) -> int:
    if not ts_str:
        return int(time.time())
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except Exception:
        return int(time.time())


# ── Claude Code ──────────────────────────────────────────────

def parse_claude_code_jsonl(path: str, project: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    session_id = Path(path).name
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "assistant":
                    continue
                msg = obj.get("message") or {}
                usage = msg.get("usage") or {}
                model = msg.get("model")
                input_t  = int(usage.get("input_tokens", 0))
                output_t = int(usage.get("output_tokens", 0))
                cache_w  = int(usage.get("cache_creation_input_tokens", 0))
                cache_r  = int(usage.get("cache_read_input_tokens", 0))
                cost     = float(obj.get("costUSD") or _calc_cost(model, input_t, output_t))
                ts       = _parse_ts(obj.get("timestamp"))
                events.append({
                    "tool": "claude_code",
                    "ts": ts,
                    "model": model,
                    "project": project,
                    "session_id": session_id,
                    "input_tokens": input_t,
                    "output_tokens": output_t,
                    "cache_read_tokens": cache_r,
                    "cache_write_tokens": cache_w,
                    "cost_usd": cost,
                })
    except OSError:
        pass
    return events


def scan_claude_code(base_dir: str | None = None) -> list[dict[str, Any]]:
    if base_dir is None:
        base_dir = str(Path.home() / ".claude" / "projects")
    root = Path(base_dir)
    if not root.exists():
        return []
    events: list[dict[str, Any]] = []
    for jsonl_file in sorted(root.rglob("*.jsonl")):
        project = jsonl_file.parent.name
        events.extend(parse_claude_code_jsonl(str(jsonl_file), project))
    return events


# ── Codex ────────────────────────────────────────────────────

def parse_codex_jsonl(path: str, project: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    session_id = Path(path).name
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("role") != "assistant":
                    continue
                usage    = obj.get("usage") or {}
                model    = obj.get("model")
                input_t  = int(usage.get("prompt_tokens", 0))
                output_t = int(usage.get("completion_tokens", 0))
                cost     = float(obj.get("cost") or _calc_cost(model, input_t, output_t))
                ts       = _parse_ts(obj.get("timestamp"))
                events.append({
                    "tool": "codex",
                    "ts": ts,
                    "model": model,
                    "project": project,
                    "session_id": session_id,
                    "input_tokens": input_t,
                    "output_tokens": output_t,
                    "cache_read_tokens": 0,
                    "cache_write_tokens": 0,
                    "cost_usd": cost,
                })
    except OSError:
        pass
    return events


def scan_codex(base_dir: str | None = None) -> list[dict[str, Any]]:
    if base_dir is None:
        base_dir = str(Path.home() / ".codex" / "sessions")
    root = Path(base_dir)
    if not root.exists():
        return []
    events: list[dict[str, Any]] = []
    for jsonl_file in sorted(root.rglob("*.jsonl")):
        project = jsonl_file.parent.name
        events.extend(parse_codex_jsonl(str(jsonl_file), project))
    return events


# ── Antigravity Language Server ───────────────────────────────

async def fetch_antigravity_ls(
    port: int, timeout: float = 1.0
) -> dict[str, Any]:
    if not _AIOHTTP or port == 0:
        return {"status": "offline"}
    url = f"http://localhost:{port}/usage"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                if resp.status != 200:
                    return {"status": "offline"}
                data = await resp.json()
                usage = data.get("usage") or {}
                model = data.get("model")
                input_t  = int(usage.get("inputTokens", 0))
                output_t = int(usage.get("outputTokens", 0))
                cache_r  = int(usage.get("cachedTokens", 0))
                cost     = float(data.get("cost") or _calc_cost(model, input_t, output_t))
                ts       = _parse_ts(data.get("timestamp"))
                return {
                    "status": "live",
                    "events": [{
                        "tool": "antigravity",
                        "ts": ts,
                        "model": model,
                        "project": None,
                        "session_id": f"ls-{ts}",
                        "input_tokens": input_t,
                        "output_tokens": output_t,
                        "cache_read_tokens": cache_r,
                        "cache_write_tokens": 0,
                        "cost_usd": cost,
                    }],
                }
    except Exception:
        return {"status": "offline"}
