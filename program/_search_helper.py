import asyncio
import aiohttp
from urllib.parse import unquote, quote_plus

# سيرفرات Piped مفتوحة - بيتجاوز bot detection يوتيوب تماماً
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


async def _piped_search(query: str) -> list | None:
    """بحث عبر Piped API"""
    for instance in PIPED_INSTANCES:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
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


async def _piped_stream(vid_id: str, audio_only: bool = True) -> str | None:
    """جيب رابط البث من Piped"""
    for instance in PIPED_INSTANCES:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(f"{instance}/streams/{vid_id}") as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    if audio_only:
                        streams = data.get("audioStreams", [])
                        # رتب من الأعلى جودة للأقل
                        streams = sorted(streams, key=lambda x: x.get("bitrate", 0), reverse=True)
                        for s in streams:
                            url = s.get("url", "")
                            if url.startswith("http"):
                                return url
                    else:
                        streams = data.get("videoStreams", [])
                        # اختار 720p أو الأقل
                        for quality in [720, 480, 360]:
                            for s in streams:
                                if s.get("quality", "") == f"{quality}p":
                                    url = s.get("url", "")
                                    if url.startswith("http"):
                                        return url
                        # لو مش لقى quality معينة خد الأول
                        if streams:
                            return streams[0].get("url", "")
        except Exception:
            continue
    return None


async def ytsearch(query: str):
    try:
        res = await _piped_search(query)
        return res if res else "لم يتم العثور على نتائج"
    except Exception as e:
        return str(e)


async def ytdl_audio(link: str):
    try:
        # استخرج video ID
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
        return 0, "فشل في جلب رابط الفيديو"
    except Exception as e:
        return 0, str(e)
