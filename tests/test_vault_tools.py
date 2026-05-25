import pytest
from pathlib import Path
import vault_tools


@pytest.fixture(autouse=True)
def vault_dir(tmp_path):
    vault_tools.set_vault_root(str(tmp_path))
    return tmp_path


def test_vault_read(vault_dir):
    (vault_dir / "test.md").write_text("hello", encoding="utf-8")
    assert vault_tools.vault_read("test.md") == "hello"


def test_vault_write_creates_parent_dirs(vault_dir):
    vault_tools.vault_write("wiki/concepts/test.md", "content")
    assert (vault_dir / "wiki" / "concepts" / "test.md").read_text(encoding="utf-8") == "content"


def test_vault_write_overwrites(vault_dir):
    vault_tools.vault_write("a.md", "first")
    vault_tools.vault_write("a.md", "second")
    assert vault_tools.vault_read("a.md") == "second"


def test_vault_list_returns_relative_paths(vault_dir):
    (vault_dir / "wiki").mkdir()
    (vault_dir / "wiki" / "a.md").write_text("a", encoding="utf-8")
    (vault_dir / "wiki" / "b.md").write_text("b", encoding="utf-8")
    result = vault_tools.vault_list("wiki")
    assert len(result) == 2
    assert all(p.startswith("wiki") for p in result)


def test_vault_list_empty_dir(vault_dir):
    (vault_dir / "empty").mkdir()
    assert vault_tools.vault_list("empty") == []


def test_vault_list_nonexistent_dir(vault_dir):
    assert vault_tools.vault_list("does_not_exist") == []


def test_vault_append(vault_dir):
    vault_tools.vault_append("log.md", "line1\n")
    vault_tools.vault_append("log.md", "line2\n")
    assert vault_tools.vault_read("log.md") == "line1\nline2\n"


def test_vault_append_creates_file(vault_dir):
    vault_tools.vault_append("new.md", "hello\n")
    assert (vault_dir / "new.md").exists()


def test_path_traversal_denied(vault_dir):
    with pytest.raises(ValueError, match="Path traversal"):
        vault_tools.vault_read("../../etc/passwd")


def test_execute_tool_vault_read(vault_dir):
    (vault_dir / "x.md").write_text("data", encoding="utf-8")
    result = vault_tools.execute_tool("vault_read", {"path": "x.md"})
    assert result == "data"


def test_execute_tool_unknown_raises(vault_dir):
    with pytest.raises(ValueError, match="Unknown tool"):
        vault_tools.execute_tool("nonexistent", {})
