import asyncio
import os
from program.ytsearch_core import ytsearch, ytsearch_async

AUDIO_DIR = "/tmp/tgbot_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)


async def ytdl_audio(link: str):
    """استخراج رابط الصوت عبر المحرك الجديد: Piped أولاً ثم yt-dlp احتياطي."""
    from ytdl_utils import get_audio_url
    return await asyncio.to_thread(get_audio_url, link)
