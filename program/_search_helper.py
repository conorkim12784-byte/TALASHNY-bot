import asyncio
from urllib.parse import unquote


def _fix_thumbnail(url: str, vid_id: str = "") -> str:
    """إصلاح روابط الـ thumbnail المكسورة"""
    if not url:
        return f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg" if vid_id else ""
    # لو الرابط مشفر URL encoding فكه
    if "%" in url:
        url = unquote(url)
    # لو لسه مش http استخدم الـ fallback
    if not url.startswith("http"):
        return f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg" if vid_id else ""
    return url


def _search_sync(query: str):
    """بحث على يوتيوب باستخدام yt_dlp"""
    import yt_dlp

    # طريقة 1: extract_flat مع android client
    for client in [["android_vr"], ["android"], ["mweb"], ["web_creator"]]:
        try:
            opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "extract_flat": True,
                "extractor_args": {"youtube": {"player_client": client}},
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                if not info or not info.get("entries"):
                    continue
                v = info["entries"][0]
                vid_id = v.get("id", "")
                dur = v.get("duration", 0) or 0
                m, s = divmod(int(dur), 60)
                thumb = _fix_thumbnail(v.get("thumbnail", ""), vid_id)
                return [
                    v.get("title", "Unknown"),
                    f"https://www.youtube.com/watch?v={vid_id}",
                    f"{m}:{s:02d}",
                    thumb
                ]
        except Exception:
            continue
    return None


def _get_url_sync(link: str, is_video: bool = False):
    """جيب الرابط المباشر من يوتيوب"""
    import yt_dlp

    fmt = "best[height<=720]/best" if is_video else "bestaudio/best"

    for client in [["android_vr"], ["android"], ["mweb"], ["web_creator"]]:
        try:
            opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "format": fmt,
                "extractor_args": {
                    "youtube": {
                        "player_client": client,
                        "player_skip": ["webpage", "js"],
                    }
                },
                "http_headers": {
                    "User-Agent": "com.google.android.youtube/17.36.4 (Linux; U; Android 11) gzip",
                },
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=False)
                if not info:
                    continue
                if info.get("url") and info["url"].startswith("http"):
                    return info["url"]
                for f in reversed(info.get("formats", [])):
                    u = f.get("url", "")
                    if u.startswith("http"):
                        return u
        except Exception:
            continue
    return None


async def ytsearch(query: str):
    loop = asyncio.get_event_loop()
    try:
        res = await loop.run_in_executor(None, _search_sync, query)
        return res if res else "لم يتم العثور على نتائج"
    except Exception as e:
        return str(e)


async def ytdl_audio(link: str):
    loop = asyncio.get_event_loop()
    try:
        url = await loop.run_in_executor(None, _get_url_sync, link, False)
        if url:
            return 1, url
        return 0, "فشل في جلب رابط الصوت"
    except Exception as e:
        return 0, str(e)


async def ytdl_video(link: str):
    loop = asyncio.get_event_loop()
    try:
        url = await loop.run_in_executor(None, _get_url_sync, link, True)
        if url:
            return 1, url
        return 0, "فشل في جلب رابط الفيديو"
    except Exception as e:
        return 0, str(e)
