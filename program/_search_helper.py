# _search_helper.py — بحث وتحميل عبر YouTube (youtubesearchpython + yt-dlp -g)

import asyncio
import os
from driver.utils import bash
from youtubesearchpython import VideosSearch

AUDIO_DIR = "/tmp/tgbot_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)


def _parse_duration(seconds) -> str:
    if not seconds:
        return "0:00"
    seconds = int(seconds)
    mins, s = divmod(seconds, 60)
    h, m = divmod(mins, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def ytsearch(query: str):
    """بحث على YouTube عبر youtubesearchpython"""
    try:
        search = VideosSearch(query, limit=1).result()
        data = search["result"][0]
        title = data["title"][:70]
        url = data["link"]
        duration = data["duration"]
        thumbnail = f"https://i.ytimg.com/vi/{data['id']}/hqdefault.jpg"
        print(f"[ytsearch] YouTube: {title}")
        return [title, url, duration, thumbnail]
    except Exception as e:
        print(f"[ytsearch error] {e}")
        return None


async def ytdl_audio(link: str):
    """جيب رابط مباشر للصوت من YouTube عبر yt-dlp -g (بدون تحميل)"""
    stdout, stderr = await bash(
        f'yt-dlp -g -f "bestaudio/best" {link}'
    )
    if stdout:
        print(f"[ytdl_audio] direct URL OK")
        return 1, stdout.split("\n")[0]
    print(f"[ytdl_audio error] {stderr}")
    return 0, stderr
