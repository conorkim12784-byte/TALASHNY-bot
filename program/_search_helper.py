import asyncio

# yt_dlp بس - بدون youtube_search أو youtubesearchpython
YDL_BASE = {
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
        "User-Agent": "com.google.android.youtube/17.36.4 (Linux; U; Android 11) gzip",
    },
}


def _search_sync(query: str):
    import yt_dlp
    opts = dict(YDL_BASE)
    opts["extract_flat"] = True
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        if not info or not info.get("entries"):
            return None
        v = info["entries"][0]
        dur = v.get("duration", 0) or 0
        m, s = divmod(int(dur), 60)
        vid_id = v.get("id", "")
        return [
            v.get("title", "Unknown"),
            f"https://www.youtube.com/watch?v={vid_id}",
            f"{m}:{s:02d}",
            v.get("thumbnail", "") or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
        ]


def _get_url_sync(link: str, is_video: bool = False):
    import yt_dlp
    fmt = "best[height<=720]/best" if is_video else "bestaudio/best"
    for client in [["android"], ["android_vr"], ["web"]]:
        try:
            opts = dict(YDL_BASE)
            opts["format"] = fmt
            opts["extractor_args"] = {
                "youtube": {
                    "player_client": client,
                    "player_skip": ["webpage", "js"],
                }
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=False)
                if not info:
                    continue
                # جيب أول URL شغال
                if info.get("url"):
                    return info["url"]
                fmts = info.get("formats", [])
                for f in reversed(fmts):
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
