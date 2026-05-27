import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
import vault_tools


@pytest.fixture(autouse=True)
def set_vault(tmp_path):
    # Set both the env var and the in-memory root so that importlib.reload(main)
    # inside the `app` fixture also picks up the correct tmp_path rather than
    # inheriting VAULT_PATH left over from other test modules.
    original_env = os.environ.get("VAULT_PATH")
    os.environ["VAULT_PATH"] = str(tmp_path)
    vault_tools.set_vault_root(str(tmp_path))
    (tmp_path / "feed").mkdir()
    yield
    if original_env is None:
        os.environ.pop("VAULT_PATH", None)
    else:
        os.environ["VAULT_PATH"] = original_env


@pytest.fixture()
def app():
    import importlib
    import main as m
    importlib.reload(m)
    return m.app


@pytest.mark.asyncio
async def test_feed_items_empty(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/api/feed/items")
    assert r.status_code == 200
    assert r.json()["items"] == []


@pytest.mark.asyncio
async def test_feed_refresh_ok(app):
    with patch("main.collect_all_feeds", return_value=[]):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post("/api/feed/refresh")
    assert r.status_code == 200
    assert r.json()["ok"] is True


@pytest.mark.asyncio
async def test_feed_status_not_found(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/feed/status", json={"slug": "feed/nonexistent", "status": "dismissed"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_feed_status_updates_item(app, tmp_path):
    # Write a feed item directly
    from feed.collector import FeedItem
    from feed.store import FeedStore, _item_to_md
    item = FeedItem(
        title="Test", url="https://example.com/x",
        source="TestFeed", category="news",
        fetched_at="2026-05-27T10:00:00+00:00",
    )
    store = FeedStore()
    store.write_if_new(item)
    slug = store.list_items()[0][0]  # "feed/YYYY-MM-DD-xxxx"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/feed/status", json={"slug": slug, "status": "dismissed"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    updated = store.list_items()[0][1]
    assert updated.status == "dismissed"
