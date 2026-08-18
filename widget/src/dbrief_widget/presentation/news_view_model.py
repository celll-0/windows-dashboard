"""Maps a ``NewsFeed``'s items into the view model the QML news section binds
to. Keys are camelCase, mirroring ``positions_view_model.py``.
"""
from __future__ import annotations

from ..data import NewsFeed
from ..constants import DESCRIPTION_LIMIT


def _truncate(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def build_news_feed_view_model(feed: NewsFeed) -> list[dict]:
    return [
        {
            "title": item.title,
            "url": item.url,
            "occurred": item.start,
            "description": _truncate(item.description, DESCRIPTION_LIMIT),
        }
        for item in feed.items
    ]
