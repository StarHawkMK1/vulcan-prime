from __future__ import annotations
from pathlib import Path
from typing import Any

_vault_root: Path | None = None


def set_vault_root(path: str) -> None:
    global _vault_root
    _vault_root = Path(path).resolve()


def _resolved(rel_path: str) -> Path:
    if _vault_root is None:
        raise RuntimeError("vault_root not set — call set_vault_root() first")
    target = (_vault_root / rel_path).resolve()
    if not str(target).startswith(str(_vault_root)):
        raise ValueError(f"Path traversal denied: {rel_path!r}")
    return target


def vault_read(path: str) -> str:
    return _resolved(path).read_text(encoding="utf-8")


def vault_write(path: str, content: str) -> str:
    p = _resolved(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return "ok"


def vault_list(dir: str) -> list[str]:
    p = _resolved(dir)
    if not p.is_dir():
        return []
    return [
        str(f.relative_to(_vault_root)).replace("\\", "/")
        for f in sorted(p.rglob("*.md"))
    ]


def vault_append(path: str, text: str) -> str:
    p = _resolved(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(text)
    return "ok"


def execute_tool(name: str, args: dict[str, Any]) -> Any:
    dispatch: dict[str, Any] = {
        "vault_read": lambda: vault_read(args["path"]),
        "vault_write": lambda: vault_write(args["path"], args["content"]),
        "vault_list": lambda: vault_list(args["dir"]),
        "vault_append": lambda: vault_append(args["path"], args["text"]),
    }
    if name not in dispatch:
        raise ValueError(f"Unknown tool: {name!r}")
    return dispatch[name]()


VAULT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "vault_read",
            "description": "Read a file from the vault. Returns full text content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from vault root, e.g. 'wiki/index.md'"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vault_write",
            "description": "Create or overwrite a file in the vault. Creates parent directories automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from vault root"},
                    "content": {"type": "string", "description": "Full file content to write"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vault_list",
            "description": "List all markdown files recursively in a vault directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir": {"type": "string", "description": "Relative directory path, e.g. 'wiki'"}
                },
                "required": ["dir"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vault_append",
            "description": "Append text to the end of a file. Creates the file if it does not exist. Use for log.md.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from vault root"},
                    "text": {"type": "string", "description": "Text to append"},
                },
                "required": ["path", "text"],
            },
        },
    },
]
