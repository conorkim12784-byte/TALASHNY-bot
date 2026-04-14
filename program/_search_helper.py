# _search_helper.py — بحث عبر YouTube Data API v3 + fallback عبر yt-dlp
# تشغيل الصوت عبر yt-dlp مباشرة بدون bgutil

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


def _ytsearch_api(query: str):
    """بحث على YouTube عبر Data API v3"""
    try:
        from config import YOUTUBE_API_KEY
        if not YOUTUBE_API_KEY:
            return None
        r = requests.get(
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
        print(f"[ytsearch] YouTube API OK: {title}")
        return [title, url, duration, thumbnail]
    except Exception as e:
        print(f"[ytsearch API error] {e}")
        return None


def _ytsearch_ytdlp(query: str):
    """بحث على YouTube عبر yt-dlp — fallback"""
    import yt_dlp
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "default_search": "ytsearch1",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            entries = info.get("entries") or []
            if not entries:
                return None
            item = entries[0]
            title = (item.get("title") or query)[:70]
            video_id = item.get("id") or ""
            url = item.get("url") or item.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}"
            if not url.startswith("http"):
                url = f"https://www.youtube.com/watch?v={video_id}"
            secs = int(item.get("duration") or 0)
            mins, s = divmod(secs, 60)
            h, m = divmod(mins, 60)
            duration = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
            thumbnail = item.get("thumbnail") or f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            print(f"[ytsearch] yt-dlp fallback OK: {title}")
            return [title, url, duration, thumbnail]
    except Exception as e:
        print(f"[ytsearch yt-dlp error] {e}")
        return None


def ytsearch(query: str):
    """بحث على YouTube — يجرب API أولاً ثم yt-dlp كـ fallback"""
    result = _ytsearch_api(query)
    if result:
        return result
    print("[ytsearch] API failed, trying yt-dlp fallback...")
    return _ytsearch_ytdlp(query)


async def ytdl_audio(link: str):
    """
    جيب رابط مباشر للصوت من يوتيوب.
    يجرب yt-dlp مباشرة بدون أي إضافات خارجية.
    """
    # الطريقة الأولى: yt-dlp -g مباشرة
    try:
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-g",
            "-f", "bestaudio/best",
            "--no-check-certificate",
            "--geo-bypass",
            "--no-playlist",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        if stdout:
            url = stdout.decode().strip().split("\n")[0]
            if url.startswith("http"):
                print(f"[ytdl_audio] OK via yt-dlp direct")
                return 1, url
    except asyncio.TimeoutError:
        print("[ytdl_audio] yt-dlp direct timed out")
    except Exception as e:
        print(f"[ytdl_audio] yt-dlp direct error: {e}")

    # الطريقة الثانية: yt-dlp مع cookies
    try:
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-g",
            "-f", "bestaudio/best",
            "--no-check-certificate",
            "--geo-bypass",
            "--no-playlist",
            "--cookies", "/app/cookies.txt",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        if stdout:
            url = stdout.decode().strip().split("\n")[0]
            if url.startswith("http"):
                print(f"[ytdl_audio] OK via yt-dlp + cookies")
                return 1, url
    except asyncio.TimeoutError:
        print("[ytdl_audio] yt-dlp cookies timed out")
    except Exception as e:
        print(f"[ytdl_audio] yt-dlp cookies error: {e}")

    # الطريقة الثالثة: bgutil (لو موجود)
    try:
        stdout, stderr = await bash(
            f'yt-dlp -g -f "bestaudio/best" '
            f'--extractor-args "youtubepot-bgutilscript:server_home=/bgutil/server" '
            f'--no-check-certificate "{link}"'
        )
        if stdout:
            url = stdout.split("\n")[0].strip()
            if url.startswith("http"):
                print(f"[ytdl_audio] OK via bgutil")
                return 1, url
    except Exception as e:
        print(f"[ytdl_audio] bgutil error: {e}")

    print(f"[ytdl_audio] all methods failed for: {link}")
    return 0, "فشل تحميل الرابط — تأكد من تحديث yt-dlp أو إضافة cookies.txt"
