import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock
import stream as stream_mod
import vault_tools
from agents.runner import run_agent, TRIAGE_TOOL


@pytest.fixture(autouse=True)
def setup(tmp_path):
    stream_mod._ops.clear()
    vault_tools.set_vault_root(str(tmp_path))


def _make_chunk(content: str | None = None, tool_calls: list | None = None):
    chunk = MagicMock()
    chunk.choices[0].delta.content = content
    chunk.choices[0].delta.tool_calls = tool_calls
    return chunk


async def _mock_stream(*chunks):
    async def _gen():
        for c in chunks:
            yield c
    return _gen()


async def test_simple_text_response():
    stream_mod.create_op("op1")

    async def mock_acompletion(**kwargs):
        return await _mock_stream(
            _make_chunk("Hello "),
            _make_chunk("world"),
            _make_chunk(None),
        )

    with patch("agents.runner.litellm.acompletion", side_effect=mock_acompletion):
        await run_agent("op1", "sys", "user msg", "anthropic", "claude-opus-4-7")

    state = stream_mod.get_op("op1")
    events = []
    while not state.queue.empty():
        events.append(state.queue.get_nowait())

    text_events = [e for e in events if e["type"] == "text"]
    done_events = [e for e in events if e["type"] == "done"]
    assert len(text_events) == 2
    assert "".join(e["content"] for e in text_events) == "Hello world"
    assert len(done_events) == 1
    assert done_events[0]["summary"] == "Hello world"


async def test_tool_call_executes_vault_read(tmp_path):
    (tmp_path / "note.md").write_text("vault content", encoding="utf-8")
    stream_mod.create_op("op2")

    tc_chunk = MagicMock()
    tc_chunk.choices[0].delta.content = None
    tc = MagicMock()
    tc.index = 0
    tc.id = "call_abc"
    tc.function.name = "vault_read"
    tc.function.arguments = '{"path": "note.md"}'
    tc_chunk.choices[0].delta.tool_calls = [tc]

    call_count = 0

    async def mock_acompletion(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return await _mock_stream(tc_chunk, _make_chunk(None))
        return await _mock_stream(_make_chunk("done reading"), _make_chunk(None))

    with patch("agents.runner.litellm.acompletion", side_effect=mock_acompletion):
        await run_agent("op2", "sys", "read it", "anthropic", "claude-opus-4-7")

    state = stream_mod.get_op("op2")
    events = []
    while not state.queue.empty():
        events.append(state.queue.get_nowait())

    tool_events = [e for e in events if e["type"] == "tool_call"]
    assert len(tool_events) == 1
    assert tool_events[0]["name"] == "vault_read"
    assert call_count == 2


async def test_triage_tool_pauses_for_approval():
    stream_mod.create_op("op3")

    report = {"new_concepts": ["RAG"], "extensions": [], "contradictions": [], "planned_pages": ["wiki/concepts/rag.md"]}
    tc_chunk = MagicMock()
    tc_chunk.choices[0].delta.content = None
    tc = MagicMock()
    tc.index = 0
    tc.id = "call_triage"
    tc.function.name = "request_triage_approval"
    tc.function.arguments = json.dumps(report)
    tc_chunk.choices[0].delta.tool_calls = [tc]

    call_count = 0

    async def mock_acompletion(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return await _mock_stream(tc_chunk, _make_chunk(None))
        return await _mock_stream(_make_chunk("Approved, writing pages."), _make_chunk(None))

    async def approve_after_delay():
        await asyncio.sleep(0.02)
        await stream_mod.set_approval("op3", True)

    asyncio.create_task(approve_after_delay())

    with patch("agents.runner.litellm.acompletion", side_effect=mock_acompletion):
        await run_agent("op3", "sys", "ingest", "anthropic", "claude-opus-4-7", extra_tools=[TRIAGE_TOOL])

    state = stream_mod.get_op("op3")
    events = []
    while not state.queue.empty():
        events.append(state.queue.get_nowait())

    triage_events = [e for e in events if e["type"] == "triage"]
    assert len(triage_events) == 1
    assert triage_events[0]["report"]["new_concepts"] == ["RAG"]
    assert call_count == 2


async def test_triage_rejected_sends_done_and_exits():
    stream_mod.create_op("op4")

    tc_chunk = MagicMock()
    tc_chunk.choices[0].delta.content = None
    tc = MagicMock()
    tc.index = 0
    tc.id = "call_triage2"
    tc.function.name = "request_triage_approval"
    tc.function.arguments = json.dumps({"new_concepts": [], "extensions": [], "contradictions": [], "planned_pages": []})
    tc_chunk.choices[0].delta.tool_calls = [tc]

    call_count = 0

    async def mock_acompletion(**kwargs):
        nonlocal call_count
        call_count += 1
        return await _mock_stream(tc_chunk, _make_chunk(None))

    async def reject_after_delay():
        await asyncio.sleep(0.02)
        await stream_mod.set_approval("op4", False)

    asyncio.create_task(reject_after_delay())

    with patch("agents.runner.litellm.acompletion", side_effect=mock_acompletion):
        await run_agent("op4", "sys", "ingest", "anthropic", "claude-opus-4-7", extra_tools=[TRIAGE_TOOL])

    state = stream_mod.get_op("op4")
    events = []
    while not state.queue.empty():
        events.append(state.queue.get_nowait())

    done_events = [e for e in events if e["type"] == "done"]
    assert len(done_events) == 1
    assert "Cancelled" in done_events[0]["summary"]
    assert call_count == 1
