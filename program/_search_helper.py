# _search_helper.py

import asyncio
import re as _re
import requests as _req
import os
import yt_dlp



def _clean_env() -> dict:
    env = os.environ.copy()
    for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
                "ALL_PROXY", "all_proxy", "GLOBAL_AGENT_HTTP_PROXY", "GLOBAL_AGENT_HTTPS_PROXY"]:
        env.pop(key, None)
    return env


def _parse_iso(iso: str) -> str:
    m = _re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return "0:00"
    h, mn, s = int(m.group(1) or 0), int(m.group(2) or 0), int(m.group(3) or 0)
    total = h * 3600 + mn * 60 + s
    mins, secs = divmod(total, 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"


def ytsearch(query: str):
    """بحث عبر YouTube Data API v3"""
    try:
        from config import YOUTUBE_API_KEY
        if not YOUTUBE_API_KEY:
            return None
        r = _req.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={"part": "snippet", "q": query, "type": "video",
                    "maxResults": 1, "key": YOUTUBE_API_KEY},
            timeout=10,
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        if not items:
            return None
        item = items[0]
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"][:70]
        thumbnail = item["snippet"]["thumbnails"].get("high", {}).get("url", "")
        r2 = _req.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"part": "contentDetails", "id": video_id, "key": YOUTUBE_API_KEY},
            timeout=10,
        )
        r2.raise_for_status()
        detail_items = r2.json().get("items", [])
        iso = detail_items[0]["contentDetails"]["duration"] if detail_items else "PT0S"
        duration = _parse_iso(iso)
        url = f"https://www.youtube.com/watch?v={video_id}"
        return [title, url, duration, thumbnail]
    except Exception as e:
        print(f"[ytsearch error] {e}")
        return None


async def ytdl_audio(link: str):
    """جلب stream URL للصوت عبر yt-dlp Python API"""
    clients = ["tv_embedded", "ios", "android", "web"]
    last_err = "all clients failed"

    def _get_url(client):
        ydl_opts = {
            "quiet": True,
            "no_warnings": False,
            "format": "bestaudio/best",
            "extractor_args": {"youtube": {"player_client": [client]}},
            "skip_download": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                url = info.get("url") or (info.get("formats") or [{}])[-1].get("url", "")
                return url if url and url.startswith("http") else None
        except Exception as e:
            return None

    for client in clients:
        url = await asyncio.to_thread(_get_url, client)
        if url:
            return 1, url

    return 0, last_err
