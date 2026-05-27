import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
import vault_tools
from feed.collector import FeedItem
from feed.store import FeedStore, _item_to_md, _parse_frontmatter


@pytest.fixture()
def tmp_vault(tmp_path):
    vault_tools.set_vault_root(str(tmp_path))
    (tmp_path / "feed").mkdir()
    return tmp_path


def _sample_item(**kwargs) -> FeedItem:
    defaults = dict(
        title='Test Article: with "quotes" and colons',
        url="https://example.com/article/1",
        source="TestFeed",
        category="news",
        fetched_at="2026-05-27T10:00:00+00:00",
        status="unread",
        summary="Short summary.",
    )
    defaults.update(kwargs)
    return FeedItem(**defaults)


# ── _item_to_md / _parse_frontmatter ─────────────────────────

def test_roundtrip_title_with_special_chars():
    item = _sample_item()
    md = _item_to_md(item)
    fm = _parse_frontmatter(md)
    assert fm["title"] == item.title


def test_roundtrip_url():
    item = _sample_item()
    md = _item_to_md(item)
    fm = _parse_frontmatter(md)
    assert fm["url"] == item.url


def test_roundtrip_status():
    item = _sample_item(status="dismissed")
    md = _item_to_md(item)
    fm = _parse_frontmatter(md)
    assert fm["status"] == "dismissed"


# ── FeedStore.write_if_new ────────────────────────────────────

def test_write_if_new_creates_file(tmp_vault):
    store = FeedStore()
    item = _sample_item()
    result = store.write_if_new(item)
    assert result is True
    files = list((tmp_vault / "feed").glob("*.md"))
    assert len(files) == 1


def test_write_if_new_skips_duplicate(tmp_vault):
    store = FeedStore()
    item = _sample_item()
    store.write_if_new(item)
    result = store.write_if_new(item)
    assert result is False
    files = list((tmp_vault / "feed").glob("*.md"))
    assert len(files) == 1


def test_write_if_new_allows_different_url(tmp_vault):
    store = FeedStore()
    store.write_if_new(_sample_item(url="https://example.com/1"))
    result = store.write_if_new(_sample_item(url="https://example.com/2"))
    assert result is True
    files = list((tmp_vault / "feed").glob("*.md"))
    assert len(files) == 2


# ── FeedStore.list_items ──────────────────────────────────────

def test_list_items_returns_written_items(tmp_vault):
    store = FeedStore()
    store.write_if_new(_sample_item(url="https://example.com/1"))
    store.write_if_new(_sample_item(url="https://example.com/2"))
    items = store.list_items()
    assert len(items) == 2
    slugs = [s for s, _ in items]
    assert all(s.startswith("feed/") for s in slugs)


def test_list_items_empty_dir(tmp_vault):
    store = FeedStore()
    assert store.list_items() == []


# ── FeedStore.update_status ───────────────────────────────────

def test_update_status_changes_frontmatter(tmp_vault):
    store = FeedStore()
    item = _sample_item()
    store.write_if_new(item)
    slug = store.list_items()[0][0]  # "feed/YYYY-MM-DD-xxxxxxxx"
    ok = store.update_status(slug, "dismissed")
    assert ok is True
    updated = store.list_items()[0][1]
    assert updated.status == "dismissed"


def test_update_status_returns_false_for_missing(tmp_vault):
    store = FeedStore()
    ok = store.update_status("feed/nonexistent-slug", "dismissed")
    assert ok is False
