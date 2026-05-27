import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from unittest.mock import patch, MagicMock
from feed.collector import (
    FeedItem, ChangelogEntry, RSSCollector, _url_slug,
    fetch_changelogs,
)
from feed.sources import Source, ChangelogSource


def _make_source(category: str = "news") -> Source:
    return Source("TestFeed", "testfeed", "http://example.com/rss", category)


# ── _url_slug ────────────────────────────────────────────────

def test_url_slug_is_8_chars():
    assert len(_url_slug("https://example.com")) == 8


def test_url_slug_is_deterministic():
    assert _url_slug("https://example.com") == _url_slug("https://example.com")


def test_url_slug_differs_for_different_urls():
    assert _url_slug("https://a.com") != _url_slug("https://b.com")


# ── RSSCollector ─────────────────────────────────────────────

def test_rss_collector_returns_feed_items():
    mock_feed = MagicMock()
    mock_entry = MagicMock()
    mock_entry.get.side_effect = lambda k, d="": {
        "link": "https://example.com/post/1",
        "title": "Test Article",
        "summary": "Short summary",
    }.get(k, d)
    mock_feed.entries = [mock_entry]

    with patch("feed.collector.feedparser.parse", return_value=mock_feed):
        items = RSSCollector(_make_source("news")).fetch()

    assert len(items) == 1
    assert items[0].url == "https://example.com/post/1"
    assert items[0].title == "Test Article"
    assert items[0].source == "TestFeed"
    assert items[0].category == "news"
    assert items[0].status == "unread"


def test_rss_collector_skips_entries_without_url():
    mock_feed = MagicMock()
    mock_entry = MagicMock()
    mock_entry.get.side_effect = lambda k, d="": {"link": "", "title": "No URL", "summary": ""}.get(k, d)
    mock_feed.entries = [mock_entry]

    with patch("feed.collector.feedparser.parse", return_value=mock_feed):
        items = RSSCollector(_make_source()).fetch()

    assert items == []


def test_rss_collector_caps_at_20_entries():
    mock_feed = MagicMock()
    entries = []
    for i in range(30):
        e = MagicMock()
        e.get.side_effect = lambda k, d="", i=i: {
            "link": f"https://example.com/{i}",
            "title": f"Title {i}",
            "summary": "",
        }.get(k, d)
        entries.append(e)
    mock_feed.entries = entries

    with patch("feed.collector.feedparser.parse", return_value=mock_feed):
        items = RSSCollector(_make_source()).fetch()

    assert len(items) == 20


def test_rss_collector_returns_empty_on_parse_error():
    with patch("feed.collector.feedparser.parse", side_effect=Exception("network error")):
        items = RSSCollector(_make_source()).fetch()
    assert items == []


# ── fetch_changelogs ─────────────────────────────────────────

def test_fetch_changelogs_parses_github_atom():
    mock_feed = MagicMock()
    mock_entry = MagicMock()
    mock_entry.get.side_effect = lambda k, d=None: {
        "title": "v1.8.0: improved tool use",
        "link": "https://github.com/anthropics/claude-code/releases/tag/v1.8.0",
    }.get(k, d)
    import time
    mock_entry.published_parsed = time.strptime("2026-05-20", "%Y-%m-%d")
    mock_feed.entries = [mock_entry]

    with patch("feed.collector.CHANGELOG_SOURCES", [
        ChangelogSource("Claude Code", "claude_code", "https://github.com/anthropics/claude-code/releases.atom")
    ]):
        with patch("feed.collector.feedparser.parse", return_value=mock_feed):
            entries = fetch_changelogs()

    assert len(entries) == 1
    assert entries[0].tool == "Claude Code"
    assert entries[0].version == "v1.8.0"
    assert entries[0].title == "improved tool use"
    assert entries[0].date == "2026-05-20"


def test_fetch_changelogs_returns_null_for_empty_url():
    with patch("feed.collector.CHANGELOG_SOURCES", [
        ChangelogSource("Gemini Code", "gemini_code", "")
    ]):
        entries = fetch_changelogs()

    assert len(entries) == 1
    assert entries[0].version is None
    assert entries[0].url is None


def test_fetch_changelogs_returns_null_on_error():
    with patch("feed.collector.CHANGELOG_SOURCES", [
        ChangelogSource("Claude Code", "claude_code", "https://github.com/anthropics/claude-code/releases.atom")
    ]):
        with patch("feed.collector.feedparser.parse", side_effect=Exception("timeout")):
            entries = fetch_changelogs()

    assert len(entries) == 1
    assert entries[0].version is None
