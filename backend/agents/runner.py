from __future__ import annotations
import asyncio
import json
from typing import Any
import litellm
import stream as stream_mod
from vault_tools import VAULT_TOOLS, execute_tool
from providers import build_model_string

TRIAGE_TOOL: dict = {
    "type": "function",
    "function": {
        "name": "request_triage_approval",
        "description": (
            "Before writing any wiki pages, call this tool to show the user a triage report "
            "and wait for their approval. Always call this before vault_write."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "new_concepts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "New concept/entity pages to be created",
                },
                "extensions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Existing pages that will be updated",
                },
                "contradictions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Contradictions found with existing wiki content",
                },
                "planned_pages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "All vault paths that will be written",
                },
            },
            "required": ["new_concepts", "extensions", "contradictions", "planned_pages"],
        },
    },
}


async def run_agent(
    op_id: str,
    system_prompt: str,
    user_message: str,
    provider: str,
    model: str,
    extra_tools: list[dict] | None = None,
) -> None:
    model_str = build_model_string(provider, model)
    tools = VAULT_TOOLS + (extra_tools or [])
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    try:
        while True:
            response = await litellm.acompletion(
                model=model_str,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                stream=True,
            )

            full_content = ""
            # idx → {id, name, args_str}
            tool_calls: dict[int, dict[str, str]] = {}

            async for chunk in response:
                delta = chunk.choices[0].delta

                if delta.content:
                    full_content += delta.content
                    await stream_mod.send_event(op_id, {"type": "text", "content": delta.content})

                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls:
                            tool_calls[idx] = {"id": "", "name": "", "args_str": ""}
                        if tc.id:
                            tool_calls[idx]["id"] = tc.id
                        if tc.function.name:
                            tool_calls[idx]["name"] += tc.function.name
                        if tc.function.arguments:
                            tool_calls[idx]["args_str"] += tc.function.arguments

            assistant_msg: dict[str, Any] = {"role": "assistant", "content": full_content}
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["args_str"]},
                    }
                    for tc in tool_calls.values()
                ]
            messages.append(assistant_msg)

            if not tool_calls:
                await stream_mod.send_event(op_id, {"type": "done", "summary": full_content})
                return

            for tc in tool_calls.values():
                name = tc["name"]
                args = json.loads(tc["args_str"]) if tc["args_str"] else {}

                await stream_mod.send_event(op_id, {"type": "tool_call", "name": name, "args": args})

                if name == "request_triage_approval":
                    await stream_mod.send_event(op_id, {"type": "triage", "report": args})
                    approved = await stream_mod.wait_for_approval(op_id)
                    if not approved:
                        await stream_mod.send_event(op_id, {"type": "done", "summary": "Cancelled by user."})
                        return
                    result = json.dumps({"approved": True})
                else:
                    try:
                        result = str(execute_tool(name, args))
                    except Exception as exc:
                        result = f"error: {exc}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

    except Exception as exc:
        await stream_mod.send_event(op_id, {"type": "error", "message": str(exc)})
