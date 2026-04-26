# ar_download2.py — أوامر التحميل العربية (تحميل / تحميل_موسيقي / تحميل_فيديو / بحث)
# ✅ هذا الملف هو النسخة الموحدة — تم حذف ar_downloader.py لأنه كان مكرر
# ✅ يعتمد على ytdl_utils المركزية بدون cookies

from __future__ import unicode_literals
import asyncio
import os
import requests
import wget
import yt_dlp
from pyrogram import Client
from pyrogram.types import Message
from yt_dlp import YoutubeDL
from config import BOT_USERNAME as bn
from driver.filters import command2, other_filters


async def _yt_search(query: str):
    """بحث عبر ytsearch_core بدون أي dependency خارجي"""
    from program.ytsearch_core import search_youtube_async
    results = await search_youtube_async(query, limit=1)
    if not results:
        return None
    r = results[0]
    return r["title"][:40], r["url"], r["duration"], r["thumbnail"]


@Client.on_message(command2(["تحميل", "تحميل_موسيقي"]))
async def song(_, message: Message):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply("» أرسل اسم الأغنية بعد الأمر")
    m = await message.reply("🔎 جاري البحث...")

    audio_file = None
    thumb_name = None
    try:
        res = await _yt_search(query)
        if not res:
            await m.edit("✘ لم يتم العثور على الاغنية\n\nيرجى إعطاء اسم أغنية صالح")
            return
        title, link, duration, thumbnail = res
        if thumbnail:
            thumb_name = f"/tmp/{title}.jpg"
            try:
                thumb_data = await asyncio.to_thread(requests.get, thumbnail, allow_redirects=True, timeout=10)
                with open(thumb_name, "wb") as f:
                    f.write(thumb_data.content)
            except Exception:
                thumb_name = None
    except Exception as e:
        await m.edit("✘ لم يتم العثور على الاغنية\n\nيرجى إعطاء اسم أغنية صالح")
        print(str(e))
        return

    await m.edit("📥 جاري تحميل الملف...")
    try:
        # ✅ استخدام ytdl_utils مع fallback تلقائي بين player_clients
        from ytdl_utils import download_audio_file
        audio_file, err = await asyncio.to_thread(download_audio_file, link, "/tmp/%(title).70s.%(ext)s")
        if not audio_file:
            await m.edit(f"✘ خطأ في التحميل:\n`{(err or 'Unknown')[:200]}`")
            return

        rep = f"**🎧 الرافع @{bn}**"
        secmul, dur, dur_arr = 1, 0, str(duration).split(":")
        for i in range(len(dur_arr) - 1, -1, -1):
            try:
                dur += int(float(dur_arr[i])) * secmul
            except ValueError:
                pass
            secmul *= 60

        await m.edit("📤 جاري رفع الملف...")
        await message.reply_audio(audio_file, caption=rep, thumb=thumb_name,
                                   parse_mode="md", title=title, duration=dur)
        await m.delete()
    except Exception as e:
        await m.edit(f"✘ خطأ: {e}")
        print(e)
    finally:
        for f in [audio_file, thumb_name]:
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass


# ─────────────────────────────────────────
# /تحميل_فيديو — تحميل فيديو من يوتيوب
# ─────────────────────────────────────────

def _download_video(link: str):
    """تحميل الفيديو عبر محرك Piped الجديد بدون cookies."""
    from ytdl_utils import download_video_file
    return download_video_file(link, quality=720)


@Client.on_message(command2(["تحميل_فيديو", "تحميل فيديو"]))
async def vsong(client, message: Message):
    await message.delete()
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply("» أرسل اسم الفيديو بعد الأمر")
    file_name = None
    preview = None
    try:
        res = await _yt_search(query)
        if not res:
            return await message.reply("✘ لم يتم العثور على الفيديو")
        title_v, link, _, thumbnail = res
    except Exception as e:
        return await message.reply(f"✘ خطأ في البحث: {e}")
    msg = await message.reply("📥 **جاري تحميل الفيديو...**")
    try:
        file_name, ytdl_data, err = await asyncio.to_thread(_download_video, link)
        if not file_name:
            return await msg.edit(f"🚫 **خطأ:** {err}")
    except Exception as e:
        return await msg.edit(f"🚫 **خطأ:** {e}")
    try:
        if thumbnail:
            try:
                preview = await asyncio.to_thread(wget.download, thumbnail)
            except Exception:
                preview = None
        await msg.edit("📤 **جاري رفع الفيديو...**")
        await message.reply_video(file_name, duration=int((ytdl_data or {}).get("duration_seconds") or (ytdl_data or {}).get("duration") or 0),
                                   thumb=preview, caption=title_v)
        await msg.delete()
    except Exception as e:
        print(e)
    finally:
        for f in [file_name, preview]:
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass


@Client.on_message(command2(["بحث"]))
async def search_lyrics(_, message: Message):
    await message.delete()
    rep = None
    try:
        if len(message.command) < 2:
            return await message.reply_text("» **قم بإرسال اسم الأغنية بعد الأمر**")
        query = message.text.split(None, 1)[1]
        rep = await message.reply_text("🔎 جاري البحث...")
        parts = query.split("-", 1)
        artist = parts[0].strip()
        title = parts[1].strip() if len(parts) == 2 else query.strip()
        url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
        resp = await asyncio.to_thread(requests.get, url, timeout=10)
        data = resp.json()
        if "lyrics" in data and data["lyrics"]:
            lyric_text = data["lyrics"][:4000]
            await rep.edit(f"🎵 **{query}**\n\n{lyric_text}")
        else:
            await rep.edit("✘ **لم يتم العثور على كلمات**\n\n» جرب: بحث فنان - أغنية")
    except Exception as e:
        # 🔧 إصلاح: rep ممكن تكون None لو الـ exception حصل قبلها
        if rep is not None:
            try:
                await rep.edit("✘ **لم يتم العثور على نتائج**\n\n» مثال: بحث Fairuz - Nassam Alayna")
            except Exception:
                pass
        print(e)
