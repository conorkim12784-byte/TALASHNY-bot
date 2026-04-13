# _search_helper.py — بحث وتحميل عبر SoundCloud و Piped API (بدون cookies)

import asyncio
import os
import uuid
import re as _re
import requests
import yt_dlp

AUDIO_DIR = "/tmp/tgbot_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.tokhmi.xyz",
    "https://pipedapi.moomoo.me",
    "https://api.piped.projectsegfau.lt",
    "https://pipedapi.in.projectsegfau.lt",
]


def _parse_duration(seconds) -> str:
    if not seconds:
        return "0:00"
    seconds = int(seconds)
    mins, s = divmod(seconds, 60)
    h, m = divmod(mins, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _search(query: str, source: str = "scsearch1"):
    """بحث عام — SoundCloud أو Dailymotion"""
    ydl_opts = {
        "quiet": True, "no_warnings": True,
        "extract_flat": True, "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"{source}:{query}", download=False)
            entries = info.get("entries") or []
            if not entries:
                return None
            item = entries[0]
            title = (item.get("title") or query)[:70]
            url = item.get("url") or item.get("webpage_url") or ""
            duration = _parse_duration(item.get("duration", 0))
            thumbnail = item.get("thumbnail") or ""
            return [title, url, duration, thumbnail] if url else None
    except Exception as e:
        print(f"[{source} search error] {e}")
        return None


def ytsearch(query: str):
    """بحث على SoundCloud أولاً، ثم Dailymotion"""
    result = _search(query, "scsearch1")
    if not result:
        result = _search(query, "dmsearch1")
    return result


def _get_piped_audio_url(video_id: str):
    """جيب رابط الصوت المباشر من Piped API"""
    for base in PIPED_INSTANCES:
        try:
            r = requests.get(f"{base}/streams/{video_id}", timeout=10)
            if r.status_code != 200:
                continue
            data = r.json()
            audio_streams = data.get("audioStreams", [])
            if not audio_streams:
                continue
            best = sorted(
                [s for s in audio_streams if s.get("url")],
                key=lambda x: x.get("bitrate", 0),
                reverse=True
            )
            if best:
                print(f"[piped_audio] OK from {base}")
                return best[0]["url"]
        except Exception as e:
            print(f"[piped_audio {base}] {e}")
    return None


def _sc_download(link: str, out_tpl: str):
    """تحميل صوت من SoundCloud أو Dailymotion"""
    ydl_opts = {
        "quiet": True, "no_warnings": True,
        "format": "bestaudio/best", "outtmpl": out_tpl,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        return None
    except Exception as e:
        print(f"[sc_download error] {e}")
        return str(e)


async def ytdl_audio(link: str):
    """
    جيب رابط/ملف صوت:
    - يوتيوب -> Piped API (رابط مباشر بدون cookies)
    - SoundCloud/Dailymotion -> تحميل مباشر
    """
    # لو رابط يوتيوب استخدم Piped API
    if "youtube.com" in link or "youtu.be" in link:
        match = _re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", link)
        if match:
            video_id = match.group(1)
            audio_url = await asyncio.to_thread(_get_piped_audio_url, video_id)
            if audio_url:
                return 1, audio_url

    # Fallback: تحميل من SoundCloud أو Dailymotion
    uid = uuid.uuid4().hex[:8]
    out_tpl = os.path.join(AUDIO_DIR, f"{uid}.%(ext)s")
    await asyncio.to_thread(_sc_download, link, out_tpl)
    for ff in os.listdir(AUDIO_DIR):
        if ff.startswith(uid):
            return 1, os.path.join(AUDIO_DIR, ff)

    return 0, "download failed"
