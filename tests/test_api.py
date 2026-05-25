import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

os.environ.setdefault("VAULT_PATH", "/tmp/vulcan_test_vault")


@pytest.fixture
def client(tmp_path):
    os.environ["VAULT_PATH"] = str(tmp_path)
    (tmp_path / "wiki").mkdir(parents=True)
    (tmp_path / "wiki" / "index.md").write_text("# Index\n", encoding="utf-8")
    (tmp_path / "raw").mkdir(parents=True)
    (tmp_path / "CLAUDE.md").write_text("# Rules\n", encoding="utf-8")

    import importlib
    import main as main_mod
    importlib.reload(main_mod)

    import vault_tools
    vault_tools.set_vault_root(str(tmp_path))

    with TestClient(main_mod.app) as c:
        yield c


def test_ingest_returns_op_id(client):
    with patch("main.asyncio.create_task"):
        resp = client.post("/api/ingest", json={
            "source_path": "raw/article.md",
            "provider": "anthropic",
            "model": "claude-opus-4-7",
        })
    assert resp.status_code == 200
    assert "op_id" in resp.json()


def test_query_returns_op_id(client):
    with patch("main.asyncio.create_task"):
        resp = client.post("/api/query", json={
            "question": "What is RAG?",
            "provider": "anthropic",
            "model": "claude-opus-4-7",
            "file_back": False,
        })
    assert resp.status_code == 200
    assert "op_id" in resp.json()


def test_lint_returns_op_id(client):
    with patch("main.asyncio.create_task"):
        resp = client.post("/api/lint", json={
            "provider": "anthropic",
            "model": "claude-opus-4-7",
        })
    assert resp.status_code == 200
    assert "op_id" in resp.json()


def test_approve_unknown_op_returns_404(client):
    resp = client.post("/api/approve/nonexistent", json={"approved": True})
    assert resp.status_code == 404


def test_status_returns_page_count(client, tmp_path):
    (tmp_path / "wiki" / "page1.md").write_text("# Page 1", encoding="utf-8")
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "pages" in data
    assert data["pages"] >= 1


def test_vault_list_endpoint(client, tmp_path):
    (tmp_path / "raw" / "article.md").write_text("content", encoding="utf-8")
    resp = client.get("/api/vault/list?dir=raw")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    assert any("article.md" in p for p in paths)
