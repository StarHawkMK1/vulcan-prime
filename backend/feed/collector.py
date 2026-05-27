from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

import feedparser

from feed.sources import FEED_SOURCES, CHANGELOG_SOURCES, Source


@dataclass
class FeedItem:
    title: str
    url: str
    source: str
    category: str        # "news" | "ai-official"
    fetched_at: str      # ISO 8601
    status: str = "unread"
    summary: str = ""


@dataclass
class ChangelogEntry:
    tool: str
    key: str
    version: str | None
    title: str | None
    date: str | None
    url: str | None


def _url_slug(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:8]


class RSSCollector:
    def __init__(self, source: Source) -> None:
        self.source = source

    def fetch(self) -> list[FeedItem]:
        try:
            feed = feedparser.parse(self.source.url)
        except Exception:
            return []
        items: list[FeedItem] = []
        for entry in feed.entries[:20]:
            url = entry.get("link", "")
            if not url:
                continue
            items.append(FeedItem(
                title=entry.get("title", "(no title)"),
                url=url,
                source=self.source.label,
                category=self.source.category,
                fetched_at=datetime.now(timezone.utc).isoformat(),
                summary=entry.get("summary", "")[:500],
            ))
        return items


def collect_all() -> list[FeedItem]:
    """Collect from all FEED_SOURCES. Returns items actually written (new only)."""
    from feed.store import FeedStore
    store = FeedStore()
    written: list[FeedItem] = []
    for src in FEED_SOURCES:
        try:
            for item in RSSCollector(src).fetch():
                if store.write_if_new(item):
                    written.append(item)
        except Exception:
            pass
    return written


def fetch_changelogs() -> list[ChangelogEntry]:
    """Fetch latest release from each CHANGELOG_SOURCES. Never raises."""
    entries: list[ChangelogEntry] = []
    for src in CHANGELOG_SOURCES:
        if not src.url:
            entries.append(ChangelogEntry(tool=src.tool, key=src.key,
                                          version=None, title=None, date=None, url=None))
            continue
        try:
            feed = feedparser.parse(src.url)
            if not feed.entries:
                raise ValueError("no entries")
            e = feed.entries[0]
            raw = e.get("title", "")
            if ":" in raw:
                version, _, rest = raw.partition(":")
                version = version.strip()
                title = rest.strip()
            else:
                version = raw.strip() or None
                title = raw.strip() or None
            date_str: str | None = None
            pp = getattr(e, "published_parsed", None)
            if pp:
                date_str = datetime(*pp[:3]).strftime("%Y-%m-%d")
            entries.append(ChangelogEntry(
                tool=src.tool, key=src.key,
                version=version or None,
                title=title or None,
                date=date_str,
                url=e.get("link"),
            ))
        except Exception:
            entries.append(ChangelogEntry(tool=src.tool, key=src.key,
                                          version=None, title=None, date=None, url=None))
    return entries
