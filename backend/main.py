from __future__ import annotations
import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import stream as stream_mod
import vault_tools
from agents.runner import run_agent
from agents.ingest import INGEST_SYSTEM_PROMPT, get_ingest_tools, get_ingest_user_message
from agents.query import QUERY_SYSTEM_PROMPT, get_query_user_message
from agents.lint import LINT_SYSTEM_PROMPT, get_lint_user_message

load_dotenv()
vault_tools.set_vault_root(os.getenv("VAULT_PATH", "./vault"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
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


@app.post("/api/ingest")
async def ingest(req: IngestRequest):
    op_id = str(uuid.uuid4())
    stream_mod.create_op(op_id)
    system = _base_system_prompt() + INGEST_SYSTEM_PROMPT
    msg = get_ingest_user_message(req.source_path)
    asyncio.create_task(
        run_agent(op_id, system, msg, req.provider, req.model, get_ingest_tools())
    )
    stream_mod.record_op("ingest", req.source_path)
    return {"op_id": op_id}


@app.post("/api/query")
async def query(req: QueryRequest):
    op_id = str(uuid.uuid4())
    stream_mod.create_op(op_id)
    system = _base_system_prompt() + QUERY_SYSTEM_PROMPT
    msg = get_query_user_message(req.question, req.file_back)
    asyncio.create_task(run_agent(op_id, system, msg, req.provider, req.model))
    stream_mod.record_op("query", req.question[:80])
    return {"op_id": op_id}


@app.post("/api/lint")
async def lint(req: LintRequest):
    op_id = str(uuid.uuid4())
    stream_mod.create_op(op_id)
    system = _base_system_prompt() + LINT_SYSTEM_PROMPT
    asyncio.create_task(run_agent(op_id, system, get_lint_user_message(), req.provider, req.model))
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


@app.get("/api/status")
async def status():
    vault_path = Path(os.getenv("VAULT_PATH", "./vault"))
    wiki_dir = vault_path / "wiki"
    pages = len(list(wiki_dir.rglob("*.md"))) if wiki_dir.exists() else 0
    return {
        "tokens": 0,
        "cost": 0.0,
        "pages": pages,
        "recent_ops": stream_mod.get_recent_ops(),
    }


@app.get("/api/vault/list")
async def vault_list(dir: str = "raw"):
    return {"paths": vault_tools.vault_list(dir)}
