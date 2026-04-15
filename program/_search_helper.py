# _search_helper.py — بحث + تشغيل بدون API أو cookies أو proxy

import asyncio
import os
import yt_dlp

AUDIO_DIR = "/tmp/tgbot_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)


def ytsearch(query: str):
    """بحث على YouTube — youtube-search-python بدون API"""
    try:
        from youtubesearchpython import VideosSearch
        results = VideosSearch(query, limit=1).result()
        items = results.get("result", [])
        if not items:
            print("[ytsearch] no results")
            return None
        item = items[0]
        title = (item.get("title") or query)[:70]
        url = item.get("link") or ""
        duration_raw = item.get("duration") or "0:00"
        thumbnail = ""
        thumbs = item.get("thumbnails") or []
        if thumbs:
            thumbnail = thumbs[-1].get("url") or ""
        print(f"[ytsearch] OK: {title}")
        return [title, url, duration_raw, thumbnail]
    except Exception as e:
        print(f"[ytsearch error] {e}")
        return None


async def ytdl_audio(link: str):
    """جيب رابط مباشر للصوت — yt-dlp Python API بدون cookies"""
    def _get():
        clients = ["mweb", "ios", "tv_embedded", "web"]
        for client in clients:
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "skip_download": True,
                "extractor_args": {
                    "youtube": {
                        "player_client": [client],
                        "skip": ["hls", "dash"],
                    }
                },
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link, download=False)
                    url = info.get("url")
                    if not url and info.get("requested_formats"):
                        url = info["requested_formats"][0].get("url")
                    if url:
                        print(f"[ytdl_audio] OK via client={client}")
                        return 1, url
            except Exception as e:
                print(f"[ytdl_audio] client={client} failed: {str(e)[:100]}")
        return 0, "all clients failed"

    return await asyncio.to_thread(_get)
