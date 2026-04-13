# _search_helper.py — بحث عبر YouTube Data API v3 + تشغيل عبر yt-dlp

import asyncio
import os
import re as _re
import requests
from driver.utils import bash

AUDIO_DIR = "/tmp/tgbot_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)


def _parse_iso_duration(iso: str) -> str:
    mt = _re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not mt:
        return "0:00"
    h, m, s = (int(mt.group(i) or 0) for i in (1, 2, 3))
    total = h * 3600 + m * 60 + s
    mins, secs = divmod(total, 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"


def ytsearch(query: str):
    """بحث على YouTube عبر Data API v3"""
    try:
        from config import YOUTUBE_API_KEY
        r = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={"part": "snippet", "q": query, "type": "video",
                    "maxResults": 1, "key": YOUTUBE_API_KEY},
            timeout=10,
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        if not items:
            print("[ytsearch] no results from API")
            return None
        item = items[0]
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"][:70]
        thumbnail = item["snippet"]["thumbnails"].get("high", {}).get("url", "")
        r2 = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"part": "contentDetails", "id": video_id, "key": YOUTUBE_API_KEY},
            timeout=10,
        )
        r2.raise_for_status()
        detail = r2.json().get("items", [])
        iso = detail[0]["contentDetails"]["duration"] if detail else "PT0S"
        duration = _parse_iso_duration(iso)
        url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"[ytsearch] YouTube API: {title}")
        return [title, url, duration, thumbnail]
    except Exception as e:
        print(f"[ytsearch error] {e}")
        return None


async def ytdl_audio(link: str):
    """جيب رابط مباشر للصوت — بيجرب tv_embedded ثم ios ثم web_creator"""
    clients = ["tv_embedded", "ios", "web_creator"]
    for client in clients:
        stdout, stderr = await bash(
            f'yt-dlp -g -f "bestaudio/best" '
            f'--extractor-args "youtube:player_client={client}" '
            f'--js-runtimes nodejs '
            f'--no-check-certificate "{link}"'
        )
        if stdout:
            url = stdout.split("\n")[0].strip()
            if url:
                print(f"[ytdl_audio] OK via {client}")
                return 1, url
        print(f"[ytdl_audio] {client} failed: {stderr[:100]}")
    return 0, "failed all clients"
