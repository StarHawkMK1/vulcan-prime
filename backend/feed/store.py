from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import vault_tools
from feed.collector import FeedItem, _url_slug


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _item_to_md(item: FeedItem) -> str:
    lines = [
        "---",
        f"title: {json.dumps(item.title, ensure_ascii=False)}",
        f"url: {json.dumps(item.url)}",
        f"source: {json.dumps(item.source, ensure_ascii=False)}",
        f"category: {json.dumps(item.category)}",
        f"status: {json.dumps(item.status)}",
        f"fetched_at: {json.dumps(item.fetched_at)}",
        "---",
        "",
        item.summary,
    ]
    return "\n".join(lines)


def _parse_frontmatter(content: str) -> dict:
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return {}
    result: dict = {}
    for line in fm_match.group(1).splitlines():
        if ": " in line:
            k, _, raw_v = line.partition(": ")
            try:
                result[k.strip()] = json.loads(raw_v.strip())
            except Exception:
                result[k.strip()] = raw_v.strip()
    return result


class FeedStore:
    def _slug_for_url(self, url: str) -> str:
        return f"{_today()}-{_url_slug(url)}"

    def _vault_path(self, slug: str) -> str:
        # slug may already include "feed/" prefix (from list_items) or not
        if slug.startswith("feed/"):
            return slug if slug.endswith(".md") else slug + ".md"
        return f"feed/{slug}.md"

    def write_if_new(self, item: FeedItem) -> bool:
        slug = self._slug_for_url(item.url)
        path = f"feed/{slug}.md"
        try:
            vault_tools.vault_read(path)
            return False  # already exists
        except Exception:
            pass
        vault_tools.vault_write(path, _item_to_md(item))
        return True

    def list_items(self) -> list[tuple[str, FeedItem]]:
        """Return list of (vault_path, FeedItem) sorted by fetched_at descending."""
        paths = vault_tools.vault_list("feed")
        result: list[tuple[str, FeedItem]] = []
        for path in paths:
            try:
                content = vault_tools.vault_read(path)
                fm = _parse_frontmatter(content)
                if not fm.get("url"):
                    continue
                body_match = re.search(r"^---\n.*?\n---\n\n?(.*)", content, re.DOTALL)
                summary = body_match.group(1).strip() if body_match else ""
                result.append((path, FeedItem(
                    title=fm.get("title", ""),
                    url=fm.get("url", ""),
                    source=fm.get("source", ""),
                    category=fm.get("category", "news"),
                    fetched_at=fm.get("fetched_at", ""),
                    status=fm.get("status", "unread"),
                    summary=summary,
                )))
            except Exception:
                pass
        result.sort(key=lambda x: x[1].fetched_at, reverse=True)
        return result

    def update_status(self, slug: str, new_status: str) -> bool:
        path = self._vault_path(slug)
        try:
            content = vault_tools.vault_read(path)
        except Exception:
            return False
        updated = re.sub(
            r'^status: .*$',
            f'status: {json.dumps(new_status)}',
            content,
            flags=re.MULTILINE,
        )
        vault_tools.vault_write(path, updated)
        return True
