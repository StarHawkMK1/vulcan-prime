from __future__ import annotations
import asyncio
import json
from collections import deque
from datetime import datetime, timezone
from typing import Any, AsyncIterator
from dataclasses import dataclass, field


@dataclass
class _OpState:
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    approval_event: asyncio.Event = field(default_factory=asyncio.Event)
    approval_result: bool = False


_ops: dict[str, _OpState] = {}
_recent_ops: deque[dict[str, Any]] = deque(maxlen=20)


def create_op(op_id: str) -> None:
    if op_id in _ops:
        raise ValueError(f"op {op_id!r} already exists")
    _ops[op_id] = _OpState()


def get_op(op_id: str) -> _OpState | None:
    return _ops.get(op_id)


async def send_event(op_id: str, event: dict[str, Any]) -> None:
    state = _ops.get(op_id)
    if state:
        await state.queue.put(event)


async def set_approval(op_id: str, approved: bool) -> bool:
    state = _ops.get(op_id)
    if not state:
        return False
    state.approval_result = approved
    state.approval_event.set()
    return True


async def wait_for_approval(op_id: str, timeout: float | None = None) -> bool:
    state = _ops.get(op_id)
    if not state:
        return False
    try:
        await asyncio.wait_for(state.approval_event.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        return False
    state.approval_event.clear()
    return state.approval_result


async def event_stream(op_id: str) -> AsyncIterator[str]:
    state = _ops.get(op_id)
    if not state:
        yield f"data: {json.dumps({'type': 'error', 'message': f'op {op_id!r} not found'})}\n\n"
        return
    try:
        while True:
            event = await state.queue.get()
            yield f"data: {json.dumps(event)}\n\n"
            if event.get("type") in ("done", "error"):
                break
    finally:
        _ops.pop(op_id, None)


def record_op(op_type: str, detail: str) -> None:
    _recent_ops.appendleft({
        "type": op_type,
        "detail": detail,
        "ts": datetime.now(timezone.utc).isoformat(),
    })


def get_recent_ops() -> list[dict[str, Any]]:
    return list(_recent_ops)
