from __future__ import annotations
import asyncio
import os
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

import stream as stream_mod
import vault_tools
from agents.runner import run_agent
from agents.ingest import INGEST_SYSTEM_PROMPT, get_ingest_tools, get_ingest_user_message
from agents.query import QUERY_SYSTEM_PROMPT, get_query_user_message
from agents.lint import LINT_SYSTEM_PROMPT, get_lint_user_message
from metering.db import MeteringDB
from metering.scanner import scan_claude_code, scan_codex, fetch_antigravity_ls
from metering.aggregator import build_dashboard_payload, week_start, today_start
from feed.collector import collect_all as collect_all_feeds, fetch_changelogs
from feed.store import FeedStore

import re as _re

def _validate_feed_slug(slug: str) -> bool:
    """Accept only safe feed slugs: feed/YYYY-MM-DD-xxxxxxxx or feed/YYYY-MM-DD-xxxxxxxx.md"""
    return bool(_re.fullmatch(r'feed/[\w-]+(?:\.md)?', slug))

load_dotenv()
_vault_path = os.getenv("VAULT_PATH")
if _vault_path:
    vault_tools.set_vault_root(_vault_path)
elif vault_tools._vault_root is None:
    vault_tools.set_vault_root("./vault")

_METERING_DB_PATH  = os.getenv("METERING_DB_PATH", ".metering.db")
_metering_db       = MeteringDB(_METERING_DB_PATH)
_metering_db.init()
_SCAN_INTERVAL     = int(os.getenv("METERING_SCAN_INTERVAL", "300"))
_AG_LS_PORT        = int(os.getenv("AG_LS_PORT", "0"))
_LIMITS = {
    "cc_5h":        int(os.getenv("CC_5H_LIMIT", "500000")),
    "cc_weekly":    int(os.getenv("CC_WEEKLY_LIMIT", "5000000")),
    "codex_5h":     int(os.getenv("CODEX_5H_LIMIT", "500000")),
    "codex_weekly": int(os.getenv("CODEX_WEEKLY_LIMIT", "5000000")),
    "ag_5h":        int(os.getenv("AG_5H_LIMIT", "0")),
    "ag_weekly":    int(os.getenv("AG_WEEKLY_LIMIT", "0")),
}
_ag_status: str = "offline"
_ag_last_seen: str | None = None
_FEED_COLLECT_INTERVAL  = int(os.getenv("FEED_COLLECT_INTERVAL",  "3600"))
_CHANGELOG_INTERVAL     = int(os.getenv("CHANGELOG_COLLECT_INTERVAL", "21600"))
_changelog_cache: list[dict] = []

_background_tasks: set[asyncio.Task] = set()


async def _do_scan() -> None:
    global _ag_status, _ag_last_seen
    cc_events = await asyncio.to_thread(scan_claude_code)
    for e in cc_events:
        _metering_db.insert_event(**e)
    cx_events = await asyncio.to_thread(scan_codex)
    for e in cx_events:
        _metering_db.insert_event(**e)
    ag = await fetch_antigravity_ls(_AG_LS_PORT)
    _ag_status = ag["status"]
    if ag["status"] == "live":
        from datetime import datetime, timezone
        _ag_last_seen = datetime.now(timezone.utc).isoformat()
        for e in ag.get("events", []):
            _metering_db.insert_event(**e)


async def _scan_loop() -> None:
    while True:
        try:
            await _do_scan()
        except Exception:
            pass
        await asyncio.sleep(_SCAN_INTERVAL)


async def _do_feed_collect() -> None:
    await asyncio.to_thread(collect_all_feeds)


async def _collect_loop() -> None:
    while True:
        try:
            await _do_feed_collect()
        except Exception:
            pass
        await asyncio.sleep(_FEED_COLLECT_INTERVAL)


async def _changelog_loop() -> None:
    global _changelog_cache
    while True:
        try:
            entries = await asyncio.to_thread(fetch_changelogs)
            _changelog_cache = [
                {"tool": e.tool, "key": e.key, "version": e.version,
                 "title": e.title, "date": e.date, "url": e.url}
                for e in entries
            ]
        except Exception:
            pass
        await asyncio.sleep(_CHANGELOG_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    for coro in [_scan_loop(), _collect_loop(), _changelog_loop()]:
        t = asyncio.create_task(coro)
        _background_tasks.add(t)
        t.add_done_callback(_background_tasks.discard)
    yield
    for task in list(_background_tasks):
        task.cancel()
    await asyncio.gather(*_background_tasks, return_exceptions=True)


app = FastAPI(lifespan=lifespan)
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _base_system_prompt() -> str:
    try:
        return vault_tools.vault_read("CLAUDE.md") + "\n\n"
    except Exception:
        return ""


class IngestRequest(BaseModel):
    source_path: str
    provider: str = "anthropic"
    model: str = "claude-opus-4-7"


class QueryRequest(BaseModel):
    question: str
    provider: str = "anthropic"
    model: str = "claude-opus-4-7"
    file_back: bool = False


class LintRequest(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-opus-4-7"


class ApproveRequest(BaseModel):
    approved: bool


class FeedStatusRequest(BaseModel):
    slug: str
    status: str  # "unread" | "ingested" | "dismissed"

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {'unread', 'ingested', 'dismissed'}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class FeedIngestRequest(BaseModel):
    slugs: list[str]
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"


@app.post("/api/ingest")
async def ingest(req: IngestRequest):
    op_id = str(uuid.uuid4())
    stream_mod.create_op(op_id)
    system = _base_system_prompt() + INGEST_SYSTEM_PROMPT
    msg = get_ingest_user_message(req.source_path)
    task = asyncio.create_task(
        run_agent(op_id, system, msg, req.provider, req.model, get_ingest_tools())
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    stream_mod.record_op("ingest", req.source_path)
    return {"op_id": op_id}


@app.post("/api/query")
async def query(req: QueryRequest):
    op_id = str(uuid.uuid4())
    stream_mod.create_op(op_id)
    system = _base_system_prompt() + QUERY_SYSTEM_PROMPT
    msg = get_query_user_message(req.question, req.file_back)
    task = asyncio.create_task(run_agent(op_id, system, msg, req.provider, req.model))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    stream_mod.record_op("query", req.question[:80])
    return {"op_id": op_id}


@app.post("/api/lint")
async def lint(req: LintRequest):
    op_id = str(uuid.uuid4())
    stream_mod.create_op(op_id)
    system = _base_system_prompt() + LINT_SYSTEM_PROMPT
    task = asyncio.create_task(run_agent(op_id, system, get_lint_user_message(), req.provider, req.model))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    stream_mod.record_op("lint", "full wiki scan")
    return {"op_id": op_id}


@app.get("/api/stream/{op_id}")
async def stream_events(op_id: str):
    return StreamingResponse(
        stream_mod.event_stream(op_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/approve/{op_id}")
async def approve(op_id: str, req: ApproveRequest):
    ok = await stream_mod.set_approval(op_id, req.approved)
    if not ok:
        raise HTTPException(status_code=404, detail=f"op {op_id!r} not found")
    return {"ok": True}


@app.get("/api/metering/dashboard")
async def metering_dashboard():
    import time
    now = int(time.time())
    payload = build_dashboard_payload(
        db=_metering_db, now=now,
        week_start_ts=week_start(now),
        today_start_ts=today_start(now),
        limits=_LIMITS,
        ag_status=_ag_status,
        ag_last_seen=_ag_last_seen,
    )
    payload["changelogs"] = _changelog_cache
    return payload


@app.post("/api/metering/refresh")
async def metering_refresh():
    await _do_scan()
    from datetime import datetime, timezone
    return {"ok": True, "scanned_at": datetime.now(timezone.utc).isoformat()}


@app.post("/api/metering/export")
async def metering_export():
    import time
    from datetime import datetime, timezone
    now = int(time.time())
    dt  = datetime.fromtimestamp(now, tz=timezone.utc)
    period = dt.strftime("%Y-%m")

    payload = build_dashboard_payload(
        db=_metering_db, now=now,
        week_start_ts=week_start(now),
        today_start_ts=today_start(now),
        limits=_LIMITS,
        ag_status=_ag_status,
        ag_last_seen=_ag_last_seen,
    )
    wt = payload["weekly_total"]
    tools = payload["tools"]

    def _fmt(n):
        if n is None: return "—"
        return f"{n:,}"

    def _cfmt(c):
        if c is None: return "—"
        return f"${c:.2f}"

    rows = "\n".join(
        f"| {name} | {_fmt(tools[key]['weekly']['tokens'])} | {_cfmt(tools[key]['weekly']['cost_usd'])} |"
        for name, key in [("Claude Code", "claude_code"), ("Codex", "codex"), ("Antigravity", "antigravity")]
    )
    daily = "\n".join(
        f"| {e['date']} | {_fmt(e.get('claude_code'))} | {_fmt(e.get('codex'))} | {_fmt(e.get('antigravity'))} | ${e['cost_usd']:.2f} |"
        for e in payload["trend_7d"]
    )

    md = f"""---
title: Metering — {period}
period: {period}
generated: {dt.isoformat()}
total_cost_usd: {wt['cost_usd']}
---

## {period} Usage Summary

| Tool | Tokens (week) | Cost (week) |
|------|---------------|-------------|
{rows}
| **Total** | **{_fmt(wt['tokens'])}** | **${wt['cost_usd']:.2f}** |

## Daily Breakdown (last 7 days)

| Date | CC Tokens | CX Tokens | AG Tokens | Cost |
|------|-----------|-----------|-----------|------|
{daily}
"""
    vault_tools.vault_write(f".metering/{period}.md", md)
    return {"ok": True, "path": f".metering/{period}.md"}


@app.get("/api/status")
async def status():
    wiki_paths = vault_tools.vault_list("wiki")
    return {
        "tokens": 0,
        "cost": 0.0,
        "pages": len(wiki_paths),
        "recent_ops": stream_mod.get_recent_ops(),
    }


@app.get("/api/vault/list")
async def vault_list(dir: str = "raw"):
    return {"paths": vault_tools.vault_list(dir)}


@app.get("/api/feed/items")
async def feed_items():
    store = FeedStore()
    return {"items": [
        {"slug": slug, "title": item.title, "url": item.url,
         "source": item.source, "category": item.category,
         "status": item.status, "fetched_at": item.fetched_at,
         "summary": item.summary}
        for slug, item in store.list_items()
    ]}


@app.post("/api/feed/refresh")
async def feed_refresh():
    from datetime import datetime, timezone
    await _do_feed_collect()
    return {"ok": True, "collected_at": datetime.now(timezone.utc).isoformat()}


@app.post("/api/feed/status")
async def feed_status(req: FeedStatusRequest):
    if not _validate_feed_slug(req.slug):
        raise HTTPException(status_code=400, detail="Invalid slug format")
    store = FeedStore()
    ok = store.update_status(req.slug, req.status)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Feed item not found: {req.slug!r}")
    return {"ok": True}


@app.post("/api/feed/ingest")
async def feed_ingest(req: FeedIngestRequest):
    store = FeedStore()
    op_ids: list[str] = []
    for slug in req.slugs:
        if not _validate_feed_slug(slug):
            raise HTTPException(status_code=400, detail=f"Invalid slug format: {slug!r}")
        path = slug if slug.endswith(".md") else slug + ".md"
        op_id = str(uuid.uuid4())
        stream_mod.create_op(op_id)
        system = _base_system_prompt() + INGEST_SYSTEM_PROMPT
        msg = get_ingest_user_message(path)
        task = asyncio.create_task(
            run_agent(op_id, system, msg, req.provider, req.model, get_ingest_tools())
        )
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
        stream_mod.record_op("ingest", path)
        store.update_status(slug, "ingested")
        op_ids.append(op_id)
    return {"op_ids": op_ids}
