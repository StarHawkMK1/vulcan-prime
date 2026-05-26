import os
import pytest
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

os.environ.setdefault("VAULT_PATH", "/tmp/vulcan_test")
os.environ.setdefault("METERING_DB_PATH", ":memory:")
os.environ.setdefault("CC_5H_LIMIT", "500000")
os.environ.setdefault("CC_WEEKLY_LIMIT", "5000000")
os.environ.setdefault("CODEX_5H_LIMIT", "500000")
os.environ.setdefault("CODEX_WEEKLY_LIMIT", "5000000")
os.environ.setdefault("AG_5H_LIMIT", "0")
os.environ.setdefault("AG_WEEKLY_LIMIT", "0")
os.environ.setdefault("AG_LS_PORT", "0")
os.environ.setdefault("METERING_SCAN_INTERVAL", "300")


@pytest.fixture
def client(tmp_path, monkeypatch):
    os.environ["VAULT_PATH"] = str(tmp_path)
    os.environ["METERING_DB_PATH"] = str(tmp_path / "m.db")
    (tmp_path / "wiki").mkdir(parents=True)
    import importlib, main as m
    importlib.reload(m)
    monkeypatch.setattr(m, "scan_claude_code", lambda: [])
    monkeypatch.setattr(m, "scan_codex", lambda: [])
    from fastapi.testclient import TestClient
    with TestClient(m.app) as c:
        yield c


def test_metering_dashboard_returns_shape(client):
    resp = client.get("/api/metering/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "tools" in data
    assert "trend_7d" in data
    assert "weekly_total" in data
    assert "claude_code" in data["tools"]
    assert "codex" in data["tools"]
    assert "antigravity" in data["tools"]


def test_metering_refresh_ok(client):
    resp = client.post("/api/metering/refresh")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert "scanned_at" in resp.json()


def test_metering_export_creates_vault_file(client, tmp_path):
    from datetime import datetime, timezone
    metering_dir = tmp_path / ".metering"
    metering_dir.mkdir()
    resp = client.post("/api/metering/export")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    period = datetime.now(timezone.utc).strftime("%Y-%m")
    assert (metering_dir / f"{period}.md").exists()
