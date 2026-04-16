"""
ytsearch_core.py
بحث YouTube خالص بـ requests فقط — بدون httpx أو httpcore أو أي مكتبة خارجية
متوافق مع Python 3.14+
"""

import re
import json
import asyncio
import requests

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _extract_videos(data: dict, limit: int) -> list:
    """استخرج نتائج الفيديو من ytInitialData"""
    results = []
    try:
        contents = (
            data.get("contents", {})
            .get("twoColumnSearchResultsRenderer", {})
            .get("primaryContents", {})
            .get("sectionListRenderer", {})
            .get("contents", [])
        )
        for section in contents:
            items = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                vid = item.get("videoRenderer")
                if not vid:
                    continue
                vid_id = vid.get("videoId", "")
                title = "".join(r.get("text", "") for r in vid.get("title", {}).get("runs", []))
                duration = vid.get("lengthText", {}).get("simpleText", "0:00")
                views_text = (vid.get("viewCountText") or {}).get("simpleText", "")
                channel = "".join(
                    r.get("text", "")
                    for r in (vid.get("ownerText") or {}).get("runs", [])
                )
                thumb = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                url = f"https://www.youtube.com/watch?v={vid_id}"
                if vid_id and title:
                    results.append({
                        "id": vid_id,
                        "title": title[:70],
                        "url": url,
                        "duration": duration,
                        "thumbnail": thumb,
                        "channel": channel,
                        "views": views_text,
                    })
                if len(results) >= limit:
                    break
            if len(results) >= limit:
                break
    except Exception as e:
        print(f"[ytsearch_core extract error] {e}")
    return results


def search_youtube(query: str, limit: int = 1) -> list:
    """
    بحث YouTube بـ requests خالص.
    بيرجع list من dicts: [{"title", "url", "duration", "thumbnail", "id", "channel", "views"}]
    أو list فارغة لو فشل.
    """
    try:
        r = requests.get(
            "https://www.youtube.com/results",
            params={"search_query": query, "sp": "EgIQAQ=="},
            headers=_HEADERS,
            timeout=10,
        )
        if r.status_code != 200:
            print(f"[ytsearch_core] HTTP {r.status_code}")
            return []

        # استخرج ytInitialData
        match = re.search(
            r"(?:var\s+)?ytInitialData\s*=\s*(\{.+?\});\s*(?:</script>|var )",
            r.text,
            re.DOTALL,
        )
        if not match:
            print("[ytsearch_core] ytInitialData not found")
            return []

        data = json.loads(match.group(1))
        return _extract_videos(data, limit)
    except Exception as e:
        print(f"[ytsearch_core] error: {e}")
        return []


async def search_youtube_async(query: str, limit: int = 1) -> list:
    """نسخة async من search_youtube"""
    return await asyncio.to_thread(search_youtube, query, limit)


# ── دوال جاهزة بنفس interface القديم ──

def ytsearch(query: str):
    """بحث الصوت — بيرجع [title, url, duration, thumbnail] أو None"""
    results = search_youtube(query, limit=1)
    if not results:
        print(f"[ytsearch] no results for: {query}")
        return None
    r = results[0]
    print(f"[ytsearch] OK: {r['title']}")
    return [r["title"], r["url"], r["duration"], r["thumbnail"]]


def ytsearch_yt(query: str):
    """بحث الفيديو — بيرجع [title, url, duration, thumbnail] أو None"""
    return ytsearch(query)


async def ytsearch_async(query: str):
    """نسخة async — بيرجع [title, url, duration, thumbnail] أو None"""
    results = await search_youtube_async(query, limit=1)
    if not results:
        return None
    r = results[0]
    return [r["title"], r["url"], r["duration"], r["thumbnail"]]
