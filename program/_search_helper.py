import asyncio
import os
import yt_dlp
from program.ytsearch_core import ytsearch, ytsearch_async

AUDIO_DIR = "/tmp/tgbot_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)


async def ytdl_audio(link: str):
    def _get():
        clients = ["mweb", "ios", "tv_embedded", "web"]
        for client in clients:
            ydl_opts = {
                "format": "bestaudio/best", "quiet": True, "no_warnings": True,
                "nocheckcertificate": True, "skip_download": True,
                "extractor_args": {"youtube": {"player_client": [client], "skip": ["hls", "dash"]}},
                "http_headers": {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"},
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link, download=False)
                    url = info.get("url")
                    if not url and info.get("requested_formats"):
                        url = info["requested_formats"][0].get("url")
                    if url:
                        return 1, url
            except Exception as e:
                print(f"[ytdl_audio] client={client} failed: {str(e)[:100]}")
        return 0, "all clients failed"
    return await asyncio.to_thread(_get)
