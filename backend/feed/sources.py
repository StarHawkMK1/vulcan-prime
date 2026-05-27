from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    label: str
    key: str
    url: str
    category: str  # "news" | "ai-official"


@dataclass(frozen=True)
class ChangelogSource:
    tool: str
    key: str
    url: str  # empty string means unavailable


FEED_SOURCES: list[Source] = [
    Source("GeekNews",      "geeknews",   "https://news.hada.io/rss",                      "news"),
    Source("AI Times",      "aitimes",    "https://www.aitimes.com/rss/allArticle.xml",     "news"),
    Source("Anthropic",     "anthropic",  "https://www.anthropic.com/news/rss.xml",         "ai-official"),
    Source("OpenAI",        "openai",     "https://openai.com/news/rss.xml",                "ai-official"),
    Source("Google DeepMind","deepmind",  "https://deepmind.google/blog/rss.xml",           "ai-official"),
]

CHANGELOG_SOURCES: list[ChangelogSource] = [
    ChangelogSource("Claude Code",  "claude_code", "https://github.com/anthropics/claude-code/releases.atom"),
    ChangelogSource("OpenAI Codex", "codex",       "https://github.com/openai/codex/releases.atom"),
    ChangelogSource("Gemini Code",  "gemini_code", ""),  # URL TBD — leave empty to show null
]
