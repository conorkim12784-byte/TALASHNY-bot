import asyncio
import aiohttp
import os
import uuid
import subprocess
import json
from urllib.parse import quote_plus
from config import DURATION_LIMIT

DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "/tmp/talashny_audio")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Piped instances للبحث فقط (مش للـ stream)
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.tokhmi.xyz",
    "https://pipedapi.moomoo.me",
    "https://piped-api.garudalinux.org",
    "https://api.piped.yt",
    "https://pipedapi.in.projectsegfau.lt",
    "https://pipedapi.syncpundit.io",
    "https://api.piped.projectsegfau.lt",
    "https://pipedapi.r4fo.com",
    "https://piped-api.privacy.com.de",
]


# ════════════════════════════════
# البحث — Piped أولاً
# ════════════════════════════════
async def _piped_search(query: str):
    for instance in PIPED_INSTANCES:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
                url = f"{instance}/search?q={quote_plus(query)}&filter=videos"
                async with session.get(url) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    items = data.get("items", [])
                    if not items:
                        continue
                    v = items[0]
                    vid_id = v.get("url", "").replace("/watch?v=", "").split("&")[0]
                    dur_secs = v.get("duration", 0) or 0
                    # تحقق من مدة الأغنية
                    if int(dur_secs) > DURATION_LIMIT:
                        return "duration_exceeded"
                    m, s = divmod(int(dur_secs), 60)
                    thumb = v.get("thumbnail", "") or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                    return [
                        v.get("title", "Unknown"),
                        f"https://www.youtube.com/watch?v={vid_id}",
                        f"{m}:{s:02d}",
                        thumb,
                        int(dur_secs),  # العنصر الخامس: المدة بالثواني للتحقق
                    ]
        except Exception:
            continue
    return None


# البحث — youtubesearchpython fallback
async def _ytsp_search(query: str):
    try:
        from youtubesearchpython import VideosSearch
        loop = asyncio.get_event_loop()
        def _search():
            s = VideosSearch(query, limit=1)
            return s.result()
        data = await loop.run_in_executor(None, _search)
        results = data.get("result", [])
        if not results:
            return None
        v = results[0]
        vid_id = v.get("id", "")
        duration_str = v.get("duration") or "0:00"
        # تحويل المدة لثواني للتحقق
        parts = duration_str.split(":")
        try:
            if len(parts) == 3:
                dur_secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                dur_secs = int(parts[0]) * 60 + int(parts[1])
            else:
                dur_secs = int(parts[0])
        except Exception:
            dur_secs = 0
        if dur_secs > DURATION_LIMIT:
            return "duration_exceeded"
        thumbnails = v.get("thumbnails", [])
        thumb = thumbnails[-1].get("url", "") if thumbnails else f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
        return [
            v.get("title", "Unknown"),
            f"https://www.youtube.com/watch?v={vid_id}",
            duration_str,
            thumb,
            dur_secs,
        ]
    except Exception:
        return None


async def ytsearch(query: str):
    """
    بيرجع:
      - list بـ 5 عناصر [title, url, duration_str, thumb, dur_secs]  ✅
      - "duration_exceeded"  لو الأغنية أطول من الحد المسموح
      - None  لو مفيش نتائج
    """
    try:
        res = await _piped_search(query)
        if res == "duration_exceeded":
            return "duration_exceeded"
        if res:
            return res
        res = await _ytsp_search(query)
        if res == "duration_exceeded":
            return "duration_exceeded"
        if res:
            return res
        return None
    except Exception:
        return None


# ════════════════════════════════
# جلب رابط الصوت — yt-dlp أولاً (موثوق)
# ════════════════════════════════
async def _ytdlp_stream_url(link: str, audio_only: bool = True):
    """
    بيجيب direct stream URL من yt-dlp بدون تحميل.
    أسرع وأموثوق من Piped لأن الـ URL مش بينتهي بسرعة.
    """
    try:
        fmt = "bestaudio/best" if audio_only else "best[height<=?720][width<=?1280]"
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "-g", "-f", fmt,
            "--no-playlist",
            "--extractor-args", "youtube:player_client=android",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        if stdout:
            url = stdout.decode().strip().split("\n")[0]
            if url.startswith("http"):
                return url
        return None
    except Exception:
        return None


async def _ytdlp_download_audio(link: str):
    """
    Fallback: تحميل الملف لو فشل جلب الـ stream URL.
    بيحذف الملف تلقائياً بعد ما البوت يخلص منه.
    """
    try:
        import yt_dlp
        loop = asyncio.get_event_loop()
        filename = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4().hex}")

        def _download():
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "format": "bestaudio/best",
                "outtmpl": filename + ".%(ext)s",
                "noplaylist": True,
                "extractor_args": {"youtube": {"player_client": ["android"]}},
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
            if os.path.exists("cookies.txt"):
                ydl_opts["cookiefile"] = "cookies.txt"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])

        await loop.run_in_executor(None, _download)

        for ext in ["mp3", "m4a", "opus", "webm", "ogg"]:
            path = f"{filename}.{ext}"
            if os.path.exists(path):
                return path
        return None
    except Exception:
        return None


# ════════════════════════════════
# ytdl_audio — الدالة الرئيسية للصوت
# ════════════════════════════════
async def ytdl_audio(link: str):
    """
    الترتيب:
    1. yt-dlp stream URL (بدون تحميل) — الأسرع والأموثوق
    2. Piped stream URL — لو yt-dlp فشل
    3. yt-dlp تحميل كامل — آخر حل
    """
    try:
        # 1. yt-dlp مباشرة (الأولوية)
        url = await _ytdlp_stream_url(link, audio_only=True)
        if url:
            return 1, url

        # 2. Piped fallback
        vid_id = ""
        if "watch?v=" in link:
            vid_id = link.split("watch?v=")[1].split("&")[0]
        elif "youtu.be/" in link:
            vid_id = link.split("youtu.be/")[1].split("?")[0]

        if vid_id:
            piped_url = await _piped_stream_audio(vid_id)
            if piped_url:
                return 1, piped_url

        # 3. تحميل كامل كآخر حل
        path = await _ytdlp_download_audio(link)
        if path:
            return 1, path

        return 0, "فشل في جلب رابط الصوت، جرب مرة أخرى"
    except Exception as e:
        return 0, str(e)


async def _piped_stream_audio(vid_id: str):
    for instance in PIPED_INSTANCES:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{instance}/streams/{vid_id}") as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    streams = sorted(
                        data.get("audioStreams", []),
                        key=lambda x: x.get("bitrate", 0),
                        reverse=True
                    )
                    for s in streams:
                        url = s.get("url", "")
                        if url.startswith("http"):
                            return url
        except Exception:
            continue
    return None


# ════════════════════════════════
# ytdl_video — الدالة الرئيسية للفيديو
# ════════════════════════════════
async def ytdl_video(link: str):
    try:
        url = await _ytdlp_stream_url(link, audio_only=False)
        if url:
            return 1, url

        vid_id = ""
        if "watch?v=" in link:
            vid_id = link.split("watch?v=")[1].split("&")[0]
        elif "youtu.be/" in link:
            vid_id = link.split("youtu.be/")[1].split("?")[0]

        if vid_id:
            piped_url = await _piped_stream_video(vid_id)
            if piped_url:
                return 1, piped_url

        return 0, "فشل في جلب رابط الفيديو"
    except Exception as e:
        return 0, str(e)


async def _piped_stream_video(vid_id: str):
    for instance in PIPED_INSTANCES:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{instance}/streams/{vid_id}") as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    streams = data.get("videoStreams", [])
                    for quality in ["720p", "480p", "360p"]:
                        for s in streams:
                            if s.get("quality", "") == quality:
                                url = s.get("url", "")
                                if url.startswith("http"):
                                    return url
                    if streams:
                        return streams[0].get("url", "")
        except Exception:
            continue
    return None
