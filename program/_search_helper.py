# _search_helper.py - بيستخدم YouTube API للبحث و yt-dlp مع Tor للتحميل

import asyncio
import re as _re
import requests as _req
import os

TOR_PROXY = "socks5://127.0.0.1:9050"
COOKIES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cookies.txt")


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
            proxies={"http": TOR_PROXY, "https": TOR_PROXY},
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
            proxies={"http": TOR_PROXY, "https": TOR_PROXY},
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
    """جلب stream URL للصوت عبر yt-dlp مع Tor proxy"""
    clients = ["android_vr", "ios", "android", "mweb"]
    last_err = ""
    for client in clients:
        cmd = [
            "yt-dlp", "--no-playlist",
            "--extractor-args", f"youtube:player_client={client}",
            "--proxy", TOR_PROXY,
            "-g", "-f", "bestaudio",
            "--format-sort", "acodec:opus,acodec:aac,acodec:mp4a",
        ]
        if os.path.exists(COOKIES_FILE):
            cmd += ["--cookies", COOKIES_FILE]
        cmd.append(link)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            lines = [l for l in stdout.decode().strip().split("\n") if l.startswith("http")]
            if lines:
                return 1, lines[0]
        last_err = stderr.decode()

    return 0, last_err
