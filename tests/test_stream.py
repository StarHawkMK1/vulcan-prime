import asyncio
import json
import pytest
import stream


@pytest.fixture(autouse=True)
def reset():
    stream._ops.clear()
    stream._recent_ops.clear()
    yield


async def drain_stream(op_id: str, max_events: int = 20) -> list[dict]:
    events = []
    async for sse_line in stream.event_stream(op_id):
        data = sse_line.strip()
        if data.startswith("data: "):
            events.append(json.loads(data[6:]))
        if len(events) >= max_events:
            break
    return events


async def test_send_and_receive():
    stream.create_op("op1")
    await stream.send_event("op1", {"type": "text", "content": "hello"})
    await stream.send_event("op1", {"type": "done", "summary": "finished"})
    events = await drain_stream("op1")
    assert events[0] == {"type": "text", "content": "hello"}
    assert events[1] == {"type": "done", "summary": "finished"}


async def test_stream_unknown_op():
    events = await drain_stream("nonexistent")
    assert events[0]["type"] == "error"


async def test_approval_true():
    stream.create_op("op2")

    async def set_approval():
        await asyncio.sleep(0.01)
        await stream.set_approval("op2", True)

    asyncio.create_task(set_approval())
    result = await stream.wait_for_approval("op2")
    assert result is True


async def test_approval_false():
    stream.create_op("op3")

    async def set_approval():
        await asyncio.sleep(0.01)
        await stream.set_approval("op3", False)

    asyncio.create_task(set_approval())
    result = await stream.wait_for_approval("op3")
    assert result is False


async def test_set_approval_unknown_op():
    ok = await stream.set_approval("nope", True)
    assert ok is False


async def test_record_recent_op():
    stream.record_op("ingest", "raw/test.md")
    ops = stream.get_recent_ops()
    assert len(ops) == 1
    assert ops[0]["type"] == "ingest"
    assert ops[0]["detail"] == "raw/test.md"
    assert "ts" in ops[0]


async def test_recent_ops_capped_at_20():
    for i in range(25):
        stream.record_op("lint", f"run-{i}")
    assert len(stream.get_recent_ops()) == 20
