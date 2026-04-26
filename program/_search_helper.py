import asyncio
import os

from program.ytsearch_core import ytsearch, ytsearch_async
from ytdl_utils import get_audio_url

AUDIO_DIR = "/tmp/tgbot_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)


async def ytdl_audio(link: str):
    """استخراج رابط الصوت بدون cookies عبر ytdl_utils المركزي."""
    return await asyncio.to_thread(get_audio_url, link)
