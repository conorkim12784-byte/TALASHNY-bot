import asyncio

try:
    from youtubesearchpython import VideosSearch
    _USE_VSP = True
except ImportError:
    _USE_VSP = False

try:
    from youtube_search import YoutubeSearch
    _USE_YS = True
except ImportError:
    _USE_YS = False

# إعدادات yt_dlp تتخطى حماية يوتيوب
_YDL_OPTS_AUDIO = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "skip_download": True,
    "extract_flat": False,
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "web"],
            "player_skip": ["webpage", "js"],
        }
    },
    "http_headers": {
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36",
    },
}

_YDL_OPTS_VIDEO = {
    "format": "best[height<=720]/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "skip_download": True,
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "web"],
            "player_skip": ["webpage", "js"],
        }
    },
    "http_headers": {
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36",
    },
}


async def ytsearch(query: str):
    loop = asyncio.get_event_loop()
    try:
        if _USE_VSP:
            def _s():
                r = VideosSearch(query, limit=1).result()
                if not r or not r.get("result"):
                    return None
                v = r["result"][0]
                th = v.get("thumbnails", [{}])
                return [
                    v.get("title", "Unknown"),
                    v.get("link", ""),
                    v.get("duration", "0:00") or "0:00",
                    th[0].get("url", "") if th else ""
                ]
            res = await loop.run_in_executor(None, _s)
            return res if res else "no results"

        elif _USE_YS:
            def _s2():
                r = YoutubeSearch(query, max_results=1).to_dict()
                if not r:
                    return None
                v = r[0]
                return [
                    v.get("title", "Unknown"),
                    "https://www.youtube.com" + v.get("url_suffix", ""),
                    v.get("duration", "0:00"),
                    (v.get("thumbnails") or [""])[0]
                ]
            res = await loop.run_in_executor(None, _s2)
            return res if res else "no results"

        else:
            import yt_dlp
            def _s3():
                opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "noplaylist": True}
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                    if not info or not info.get("entries"):
                        return None
                    v = info["entries"][0]
                    dur = v.get("duration", 0) or 0
                    m, s = divmod(int(dur), 60)
                    return [
                        v.get("title", "Unknown"),
                        f"https://www.youtube.com/watch?v={v.get('id','')}",
                        f"{m}:{s:02d}",
                        v.get("thumbnail", "")
                    ]
            res = await loop.run_in_executor(None, _s3)
            return res if res else "no results"

    except Exception as e:
        return str(e)


def _get_direct_url(link: str, opts: dict):
    """بيجيب الرابط المباشر من يوتيوب بدون bot detection"""
    import yt_dlp
    # جرب android client الأول عشان أقل حماية
    for client in [["android"], ["android", "web"], ["web"]]:
        try:
            o = dict(opts)
            o["extractor_args"] = {"youtube": {"player_client": client}}
            with yt_dlp.YoutubeDL(o) as ydl:
                info = ydl.extract_info(link, download=False)
                if not info:
                    continue
                url = info.get("url") or (info.get("formats") or [{}])[-1].get("url", "")
                if url and url.startswith("http"):
                    return url
        except Exception:
            continue
    return None


async def ytdl_audio(link: str):
    loop = asyncio.get_event_loop()
    try:
        url = await loop.run_in_executor(None, _get_direct_url, link, _YDL_OPTS_AUDIO)
        if url:
            return 1, url
        return 0, "فشل في جلب رابط الصوت"
    except Exception as e:
        return 0, str(e)


async def ytdl_video(link: str):
    loop = asyncio.get_event_loop()
    try:
        url = await loop.run_in_executor(None, _get_direct_url, link, _YDL_OPTS_VIDEO)
        if url:
            return 1, url
        return 0, "فشل في جلب رابط الفيديو"
    except Exception as e:
        return 0, str(e)
