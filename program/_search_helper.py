import asyncio
import aiohttp
import os
import uuid
from urllib.parse import unquote, quote_plus

PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.tokhmi.xyz",
    "https://pipedapi.moomoo.me",
    "https://piped-api.garudalinux.org",
    "https://api.piped.yt",
]

# مجلد التحميل المؤقت
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "/tmp/talashny_audio")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def _fix_thumbnail(url: str, vid_id: str = "") -> str:
    if not url:
        return f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg" if vid_id else ""
    if "%" in url:
        url = unquote(url)
    if not url.startswith("http"):
        return f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg" if vid_id else ""
    return url


# ========================
# البحث
# ========================
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
                    dur = v.get("duration", 0) or 0
                    m, s = divmod(int(dur), 60)
                    thumb = v.get("thumbnail", "") or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                    return [v.get("title", "Unknown"), f"https://www.youtube.com/watch?v={vid_id}", f"{m}:{s:02d}", thumb]
        except Exception:
            continue
    return None


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
        duration = v.get("duration") or "0:00"
        thumbnails = v.get("thumbnails", [])
        thumb = thumbnails[-1].get("url", "") if thumbnails else f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
        return [v.get("title", "Unknown"), f"https://www.youtube.com/watch?v={vid_id}", duration, thumb]
    except Exception:
        return None


async def _ytdlp_search(query: str):
    try:
        import yt_dlp
        loop = asyncio.get_event_loop()
        def _search():
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": True}) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                entries = info.get("entries", [])
                if not entries:
                    return None
                v = entries[0]
                vid_id = v.get("id", "")
                dur = v.get("duration") or 0
                m, s = divmod(int(dur), 60)
                thumb = v.get("thumbnail") or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                return [v.get("title", "Unknown"), f"https://www.youtube.com/watch?v={vid_id}", f"{m}:{s:02d}", thumb]
        return await loop.run_in_executor(None, _search)
    except Exception:
        return None


async def ytsearch(query: str):
    try:
        res = await _piped_search(query)
        if res:
            return res
        res = await _ytsp_search(query)
        if res:
            return res
        res = await _ytdlp_search(query)
        if res:
            return res
        return "لم يتم العثور على نتائج"
    except Exception as e:
        return str(e)


# ========================
# التحميل المحلي بـ yt-dlp
# ========================
async def _ytdlp_download_audio(link: str) -> str | None:
    """يحمل الفيديو ويحوله لـ audio محلياً ويرجع المسار"""
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
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])

        await loop.run_in_executor(None, _download)

        # ابحث عن الملف اللي اتحمل
        for ext in ["mp3", "m4a", "opus", "webm", "ogg"]:
            path = f"{filename}.{ext}"
            if os.path.exists(path):
                return path

        return None
    except Exception:
        return None


# ========================
# Piped Stream (سريع لو شغال)
# ========================
async def _piped_stream(vid_id: str, audio_only: bool = True):
    for instance in PIPED_INSTANCES:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(f"{instance}/streams/{vid_id}") as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    if audio_only:
                        streams = sorted(data.get("audioStreams", []), key=lambda x: x.get("bitrate", 0), reverse=True)
                        for s in streams:
                            url = s.get("url", "")
                            if url.startswith("http"):
                                return url
                    else:
                        streams = data.get("videoStreams", [])
                        for quality in [720, 480, 360]:
                            for s in streams:
                                if s.get("quality", "") == f"{quality}p":
                                    url = s.get("url", "")
                                    if url.startswith("http"):
                                        return url
                        if streams:
                            return streams[0].get("url", "")
        except Exception:
            continue
    return None


# ========================
# ytdl_audio - الرئيسي
# ========================
async def ytdl_audio(link: str):
    try:
        vid_id = ""
        if "watch?v=" in link:
            vid_id = link.split("watch?v=")[1].split("&")[0]
        elif "youtu.be/" in link:
            vid_id = link.split("youtu.be/")[1].split("?")[0]

        if not vid_id:
            return 0, "رابط غير صحيح"

        # أولاً جرب Piped stream (أسرع)
        url = await _piped_stream(vid_id, audio_only=True)
        if url:
            return 1, url

        # ثانياً حمّل الملف محلياً وحوله
        path = await _ytdlp_download_audio(link)
        if path:
            return 1, path

        return 0, "فشل في جلب رابط الصوت"
    except Exception as e:
        return 0, str(e)


async def ytdl_video(link: str):
    try:
        vid_id = ""
        if "watch?v=" in link:
            vid_id = link.split("watch?v=")[1].split("&")[0]
        elif "youtu.be/" in link:
            vid_id = link.split("youtu.be/")[1].split("?")[0]

        if not vid_id:
            return 0, "رابط غير صحيح"

        url = await _piped_stream(vid_id, audio_only=False)
        if url:
            return 1, url

        path = await _ytdlp_download_audio(link)
        if path:
            return 1, path

        return 0, "فشل في جلب رابط الفيديو"
    except Exception as e:
        return 0, str(e)
