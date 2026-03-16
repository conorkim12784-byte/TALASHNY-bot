# _search_helper.py — بحث وتحميل عبر SoundCloud (مجاني بدون API key)

import asyncio
import re as _re
import os
import uuid
import yt_dlp

AUDIO_DIR = "/tmp/tgbot_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)


def _parse_duration(seconds) -> str:
    if not seconds:
        return "0:00"
    seconds = int(seconds)
    mins, secs = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"


def ytsearch(query: str):
    """بحث على SoundCloud عبر yt-dlp — مجاني بدون API"""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "default_search": "scsearch1",
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch1:{query}", download=False)
            entries = info.get("entries") or []
            if not entries:
                return None
            item = entries[0]
            title = (item.get("title") or query)[:70]
            url = item.get("url") or item.get("webpage_url") or ""
            duration = _parse_duration(item.get("duration", 0))
            thumbnail = item.get("thumbnail") or ""
            if not url:
                return None
            return [title, url, duration, thumbnail]
    except Exception as e:
        print(f"[scsearch error] {e}")
        return None


def _sc_get_url(link: str):
    """جلب stream URL من SoundCloud"""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            url = info.get("url")
            if not url:
                fmts = info.get("formats") or []
                for f in reversed(fmts):
                    if f.get("url", "").startswith("http"):
                        url = f["url"]
                        break
            return url if url and url.startswith("http") else None
    except Exception as e:
        print(f"[sc_get_url error] {e}")
        return None


def _sc_download(link: str, out_tpl: str):
    """تحميل ملف صوتي من SoundCloud"""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "outtmpl": out_tpl,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        return None
    except Exception as e:
        print(f"[sc_download error] {e}")
        return str(e)


async def ytdl_audio(link: str):
    """جلب stream URL أو تحميل ملف من SoundCloud"""
    # محاولة 1: stream URL مباشر
    url = await asyncio.to_thread(_sc_get_url, link)
    if url:
        return 1, url

    # محاولة 2: تحميل ملف محلي
    uid = uuid.uuid4().hex[:8]
    out_tpl = os.path.join(AUDIO_DIR, f"{uid}.%(ext)s")
    last_err = await asyncio.to_thread(_sc_download, link, out_tpl) or "download failed"
    for ff in os.listdir(AUDIO_DIR):
        if ff.startswith(uid):
            return 1, os.path.join(AUDIO_DIR, ff)

    return 0, last_err
