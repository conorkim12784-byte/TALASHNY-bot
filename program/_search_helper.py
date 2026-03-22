# _search_helper.py — بحث وتحميل عبر SoundCloud و Dailymotion

import asyncio
import os
import uuid
import yt_dlp

AUDIO_DIR = "/tmp/tgbot_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)


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
    """بحث على SoundCloud أولاً، لو مفيش نتيجة يجرب Dailymotion"""
    result = _search(query, "scsearch1")
    if not result:
        result = _search(query, "dmsearch1")
    return result


def _sc_download(link: str, out_tpl: str):
    """تحميل صوت من SoundCloud"""
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
        # جرب Dailymotion كـ fallback
        return str(e)


async def ytdl_audio(link: str):
    """تحميل صوت محلي"""
    uid = uuid.uuid4().hex[:8]
    out_tpl = os.path.join(AUDIO_DIR, f"{uid}.%(ext)s")
    await asyncio.to_thread(_sc_download, link, out_tpl)
    for ff in os.listdir(AUDIO_DIR):
        if ff.startswith(uid):
            return 1, os.path.join(AUDIO_DIR, ff)
    return 0, "download failed"
