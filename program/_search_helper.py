import asyncio
import aiohttp
from urllib.parse import unquote, quote_plus

# ========================
# Piped Instances (fallback 1)
# ========================
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.tokhmi.xyz",
    "https://pipedapi.moomoo.me",
    "https://piped-api.garudalinux.org",
    "https://api.piped.yt",
]


def _fix_thumbnail(url: str, vid_id: str = "") -> str:
    if not url:
        return f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg" if vid_id else ""
    if "%" in url:
        url = unquote(url)
    if not url.startswith("http"):
        return f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg" if vid_id else ""
    return url


# ========================
# Fallback 1: Piped API
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
                    return [
                        v.get("title", "Unknown"),
                        f"https://www.youtube.com/watch?v={vid_id}",
                        f"{m}:{s:02d}",
                        thumb
                    ]
        except Exception:
            continue
    return None


# ========================
# Fallback 2: youtube-search-python
# ========================
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
        thumb = ""
        thumbnails = v.get("thumbnails", [])
        if thumbnails:
            thumb = thumbnails[-1].get("url", "")
        if not thumb:
            thumb = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
        return [
            v.get("title", "Unknown"),
            f"https://www.youtube.com/watch?v={vid_id}",
            duration,
            thumb
        ]
    except Exception:
        return None


# ========================
# Fallback 3: yt-dlp
# ========================
async def _ytdlp_search(query: str):
    try:
        import yt_dlp
        loop = asyncio.get_event_loop()

        def _search():
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                entries = info.get("entries", [])
                if not entries:
                    return None
                v = entries[0]
                vid_id = v.get("id", "")
                dur = v.get("duration") or 0
                m, s = divmod(int(dur), 60)
                thumb = v.get("thumbnail") or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                return [
                    v.get("title", "Unknown"),
                    f"https://www.youtube.com/watch?v={vid_id}",
                    f"{m}:{s:02d}",
                    thumb
                ]

        return await loop.run_in_executor(None, _search)
    except Exception:
        return None


# ========================
# Main ytsearch
# ========================
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
# Piped Stream
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
                        streams = data.get("audioStreams", [])
                        streams = sorted(streams, key=lambda x: x.get("bitrate", 0), reverse=True)
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
# yt-dlp Stream Fallback
# ========================
async def _ytdlp_stream(vid_id: str, audio_only: bool = True):
    try:
        import yt_dlp
        loop = asyncio.get_event_loop()
        link = f"https://www.youtube.com/watch?v={vid_id}"

        def _get_url():
            if audio_only:
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "format": "bestaudio/best",
                    "noplaylist": True,
                }
            else:
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "format": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                    "noplaylist": True,
                }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                if audio_only:
                    return info.get("url", "")
                else:
                    formats = info.get("formats", [])
                    for f in reversed(formats):
                        if f.get("url") and f.get("vcodec") != "none":
                            return f["url"]
                    return info.get("url", "")

        return await loop.run_in_executor(None, _get_url)
    except Exception:
        return None


# ========================
# ytdl_audio / ytdl_video
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

        url = await _piped_stream(vid_id, audio_only=True)
        if url:
            return 1, url

        url = await _ytdlp_stream(vid_id, audio_only=True)
        if url:
            return 1, url

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

        url = await _ytdlp_stream(vid_id, audio_only=False)
        if url:
            return 1, url

        return 0, "فشل في جلب رابط الفيديو"
    except Exception as e:
        return 0, str(e)
