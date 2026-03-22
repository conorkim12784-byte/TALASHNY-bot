
def _get_piped_audio_url(video_id: str) -> str | None:
    """جيب رابط الصوت من Piped API"""
    import requests
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.projectsegfau.lt",
        "https://piped-api.garudalinux.org",
    ]
    for base in instances:
        try:
            r = requests.get(f"{base}/streams/{video_id}", timeout=10)
            if r.status_code != 200:
                continue
            data = r.json()
            audio_streams = data.get("audioStreams", [])
            if not audio_streams:
                continue
            best = sorted(audio_streams, key=lambda x: x.get("bitrate", 0), reverse=True)
            if best:
                return best[0]["url"]
        except Exception as e:
            print(f"[piped_audio {base}] {e}")
    return None


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


def _piped_search_audio(query: str):
    """بحث على يوتيوب عبر Piped API للصوت"""
    import requests
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.projectsegfau.lt",
        "https://piped-api.garudalinux.org",
        "https://pipedapi.adminforge.de",
    ]
    for base in instances:
        try:
            r = requests.get(
                f"{base}/search",
                params={"q": query, "filter": "videos"},
                timeout=10
            )
            if r.status_code != 200:
                continue
            items = r.json().get("items", [])
            if not items:
                continue
            item = items[0]
            vid_id = item.get("url", "").replace("/watch?v=", "")
            if not vid_id:
                continue
            title = (item.get("title") or query)[:70]
            url = f"https://www.youtube.com/watch?v={vid_id}"
            secs = int(item.get("duration") or 0)
            mins, s = divmod(secs, 60); h, m = divmod(mins, 60)
            duration = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
            thumbnail = item.get("thumbnail") or ""
            return [title, url, duration, thumbnail]
        except Exception as e:
            print(f"[piped_search_audio {base}] {e}")
    return None


def ytsearch(query: str):
    """بحث على SoundCloud أولاً، ثم Piped/YouTube، ثم Dailymotion"""
    result = _search(query, "scsearch1")
    if not result:
        result = _piped_search_audio(query)
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


def _piped_download_audio(video_id: str, out_tpl: str) -> bool:
    """تحميل صوت من Piped API"""
    import requests
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.projectsegfau.lt",
        "https://piped-api.garudalinux.org",
        "https://pipedapi.adminforge.de",
        "https://piped-api.privacy.com.de",
    ]
    for base in instances:
        try:
            r = requests.get(f"{base}/streams/{video_id}", timeout=10)
            if r.status_code != 200:
                continue
            data = r.json()
            audio_streams = data.get("audioStreams", [])
            if not audio_streams:
                continue
            best_audio = sorted(
                [s for s in audio_streams if s.get("url")],
                key=lambda x: x.get("bitrate", 0),
                reverse=True
            )
            if not best_audio:
                continue
            audio_url = best_audio[0]["url"]
            r2 = requests.get(audio_url, stream=True, timeout=60)
            fname = out_tpl.replace("%(ext)s", "m4a")
            with open(fname, "wb") as f:
                for chunk in r2.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"[piped_audio {base}] {e}")
    return False


async def ytdl_audio(link: str):
    """تحميل صوت — يجرب Piped أولاً ثم SoundCloud"""
    import re as _re
    uid = uuid.uuid4().hex[:8]
    out_tpl = os.path.join(AUDIO_DIR, f"{uid}.%(ext)s")

    # لو رابط يوتيوب جرب Piped
    match = _re.search(r"(?:v=|youtu\.be/)([\w-]{11})", link)
    if match:
        vid_id = match.group(1)
        success = await asyncio.to_thread(_piped_download_audio, vid_id, out_tpl)
        if success:
            for ff in os.listdir(AUDIO_DIR):
                if ff.startswith(uid):
                    return 1, os.path.join(AUDIO_DIR, ff)

    # Fallback: SoundCloud
    await asyncio.to_thread(_sc_download, link, out_tpl)
    for ff in os.listdir(AUDIO_DIR):
        if ff.startswith(uid):
            return 1, os.path.join(AUDIO_DIR, ff)
    return 0, "download failed"
