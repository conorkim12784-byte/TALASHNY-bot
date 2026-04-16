import re
import asyncio
import os

from config import BOT_USERNAME, IMG_1, IMG_2, IMG_5
from program.utils.inline import stream_markup
from driver.design.thumbnail import thumb
from driver.design.chatname import CHAT_TITLE
from driver.filters import command, other_filters, command2
from driver.queues import QUEUE, add_to_queue
from driver.nowplaying import current_requester
from driver.veez import call_py, user
from driver.utils import bash
from pyrogram import Client
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant, PeerIdInvalid
from pyrogram.types import InlineKeyboardMarkup, Message
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
import yt_dlp
from program.ytsearch_core import ytsearch, ytsearch_yt

DL_DIR = "/tmp/tgbot_vids"
AUDIO_DIR = "/tmp/tgbot_audio"
os.makedirs(DL_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)


def _ydl_get_url(link: str) -> tuple:
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
        }

        cookies_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cookies.txt")
        if os.path.isfile(cookies_file):
            ydl_opts["cookiefile"] = cookies_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)

            url = info.get("url")

            if not url:
                for f in info.get("formats", []):
                    if f.get("url"):
                        url = f["url"]
                        break

            if url:
                return 1, url

        return 0, "فشل استخراج الرابط"

    except Exception as e:
        print(f"[yt error] {e}")
        return 0, str(e)


async def ytdl_audio(link):
    return await asyncio.to_thread(_ydl_get_url, link)

ytdl = ytdl_audio


async def ytdl_video(link, quality=720):
    return await asyncio.to_thread(_ydl_get_url, link)


def multisearch_video(query: str):
    result = ytsearch_yt(query)
    if result and isinstance(result, list) and len(result) == 4:
        return result
    return None


def get_video_quality(Q):
    if Q == 480:
        return VideoQuality.SD_480p
    elif Q == 360:
        return VideoQuality.SD_360p
    return VideoQuality.HD_720p


async def _check_and_join(c, m, chat_id):
    try:
        aing = await c.get_me()
    except Exception as e:
        await m.reply_text(f"error:\n\n{e}")
        return False

    a = await c.get_chat_member(chat_id, aing.id)

    if a.status.value not in ("administrator", "creator"):
        await m.reply_text("💡 لازم ترفع البوت ادمن بصلاحيات كاملة")
        return False

    try:
        ubot = (await user.get_me()).id
        await c.get_chat_member(chat_id, ubot)
    except:
        try:
            invitelink = await c.export_chat_invite_link(chat_id)
            await user.join_chat(invitelink)
        except Exception as e:
            await m.reply_text(f"فشل دخول المساعد: {e}")
            return False

    return True


@Client.on_message(command(["vplay"]) & other_filters)
async def vplay(c: Client, m: Message):
    await m.delete()

    if len(m.command) < 2:
        return await m.reply("ابعت اسم او لينك")

    chat_id = m.chat.id

    if not await _check_and_join(c, m, chat_id):
        return

    msg = await m.reply("🔍 جاري البحث...")

    query = m.text.split(None, 1)[1]
    search = multisearch_video(query)

    if not search:
        return await msg.edit("❌ مفيش نتائج")

    songname, url, duration, thumbnail = search

    await msg.edit("⏳ جاري التحميل...")

    ok, link = await ytdl_video(url)

    if ok == 0:
        return await msg.edit(f"❌ فشل التحميل\n{link}")

    if chat_id in QUEUE:
        pos = add_to_queue(chat_id, songname, link, url, "Video", 720)
        return await msg.edit(f"📌 اتحط في الكيو رقم {pos}")

    await call_py.play(chat_id, MediaStream(link, AudioQuality.HIGH, VideoQuality.HD_720p))
    add_to_queue(chat_id, songname, link, url, "Video", 720)

    await msg.edit(f"▶️ شغال دلوقتي: {songname}")


@Client.on_message(command(["vstream"]) & other_filters)
async def vstream(c: Client, m: Message):
    await m.delete()

    if len(m.command) < 2:
        return await m.reply("ابعت لينك")

    link = m.text.split(None, 1)[1]
    chat_id = m.chat.id

    if not await _check_and_join(c, m, chat_id):
        return

    msg = await m.reply("⏳ جاري التشغيل...")

    ok, stream = await ytdl_audio(link)

    if ok == 0:
        return await msg.edit(f"❌ خطأ\n{stream}")

    await call_py.play(chat_id, MediaStream(stream, AudioQuality.HIGH, VideoQuality.HD_720p))
    add_to_queue(chat_id, "Live", stream, link, "Video", 720)

    await msg.edit("✅ شغال")
