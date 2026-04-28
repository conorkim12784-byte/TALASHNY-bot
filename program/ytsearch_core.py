"""
ytsearch_core.py
بحث YouTube عبر youtube-search-python (نمط النسخة القديمة) — مباشر بدون APIs خارجية.
"""

import asyncio
from ytdl_utils import search_youtube


async def search_youtube_async(query: str, limit: int = 1) -> list:
    return await asyncio.to_thread(search_youtube, query, limit)


def ytsearch(query: str):
    """يرجع [title, url, duration, thumbnail] أو None — متوافق مع النسخة القديمة."""
    results = search_youtube(query, limit=1)
    if not results:
        print(f"[ytsearch] no results for: {query}")
        return None
    r = results[0]
    print(f"[ytsearch] OK: {r['title']}")
    return [r["title"], r["url"], r["duration"], r["thumbnail"]]


def ytsearch_yt(query: str):
    return ytsearch(query)


async def ytsearch_async(query: str):
    results = await search_youtube_async(query, limit=1)
    if not results:
        return None
    r = results[0]
    return [r["title"], r["url"], r["duration"], r["thumbnail"]]
