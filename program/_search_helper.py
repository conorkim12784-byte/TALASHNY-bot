import asyncio
import os
from urllib.parse import unquote


def _fix_thumbnail(url: str, vid_id: str = "") -> str:
    if not url:
        return f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg" if vid_id else ""
    if "%" in url:
        url = unquote(url)
    if not url.startswith("http"):
        return f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg" if vid_id else ""
    return url


def _make_opts(extra: dict = {}) -> dict:
    """إعدادات yt_dlp الأساسية مع cookies لو موجودة"""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "ignoreerrors": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 Chrome/112.0.0.0 Mobile Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
    # لو في cookies.txt على السيرفر استخدمها
    for path in ["/app/cookies.txt", "cookies.txt", "/root/cookies.txt"]:
        if os.path.exists(path):
            opts["cookiefile"] = path
            break
    opts.update(extra)
    return opts


# الـ clients بالترتيب من الأقل bot-detection للأكتر
_CLIENTS = [
    ["android_vr"],
    ["android_creator"],
    ["android"],
    ["ios"],
    ["mweb"],
]


def _search_sync(query: str):
    import yt_dlp
    for client in _CLIENTS:
        try:
            opts = _make_opts({
                "extract_flat": True,
                "extractor_args": {"youtube": {"player_client": client}},
            })
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                if not info or not info.get("entries"):
                    continue
                v = info["entries"][0]
                vid_id = v.get("id", "")
                if not vid_id:
                    continue
                dur = v.get("duration", 0) or 0
                m, s = divmod(int(dur), 60)
                return [
                    v.get("title", "Unknown"),
                    f"https://www.youtube.com/watch?v={vid_id}",
                    f"{m}:{s:02d}",
                    _fix_thumbnail(v.get("thumbnail", ""), vid_id)
                ]
        except Exception:
            continue
    return None


def _get_audio_url_sync(link: str) -> str | None:
    """جيب رابط صوت فقط — بدون فيديو"""
    import yt_dlp
    # فورمات الصوت فقط بالترتيب
    audio_formats = [
        "140",          # m4a audio 128k - الأكتر توافقاً
        "251",          # webm audio opus
        "250",          # webm audio opus low
        "249",          # webm audio opus lowest
        "bestaudio[ext=m4a]",
        "bestaudio[ext=webm]",
        "bestaudio",
    ]
    for client in _CLIENTS:
        for fmt in audio_formats:
            try:
                opts = _make_opts({
                    "format": fmt,
                    "extractor_args": {
                        "youtube": {
                            "player_client": client,
                            "player_skip": ["webpage", "js"],
                        }
                    },
                })
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(link, download=False)
                    if not info:
                        continue
                    url = info.get("url", "")
                    if url and url.startswith("http"):
                        return url
                    # تحقق من formats
                    for f in reversed(info.get("formats", [])):
                        # صوت فقط بدون فيديو
                        if f.get("vcodec", "none") == "none" and f.get("acodec", "none") != "none":
                            u = f.get("url", "")
                            if u.startswith("http"):
                                return u
            except Exception:
                continue
    return None


def _get_video_url_sync(link: str) -> str | None:
    """جيب رابط فيديو"""
    import yt_dlp
    for client in _CLIENTS:
        try:
            opts = _make_opts({
                "format": "best[height<=720]/best",
                "extractor_args": {
                    "youtube": {
                        "player_client": client,
                        "player_skip": ["webpage", "js"],
                    }
                },
            })
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=False)
                if not info:
                    continue
                url = info.get("url", "")
                if url and url.startswith("http"):
                    return url
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
        url = await loop.run_in_executor(None, _get_audio_url_sync, link)
        if url:
            return 1, url
        return 0, "فشل في جلب رابط الصوت - جرب لاحقاً"
    except Exception as e:
        return 0, str(e)


async def ytdl_video(link: str):
    loop = asyncio.get_event_loop()
    try:
        url = await loop.run_in_executor(None, _get_video_url_sync, link)
        if url:
            return 1, url
        return 0, "فشل في جلب رابط الفيديو - جرب لاحقاً"
    except Exception as e:
        return 0, str(e)
