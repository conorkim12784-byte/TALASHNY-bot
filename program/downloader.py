# downloader.py — /song و /vsong و /lyric بدون API أو cookies

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
from driver.decorators import humanbytes
from driver.filters import command, other_filters


# ─────────────────────────────────────────
# بحث داخلي بدون API
# ─────────────────────────────────────────

async def _yt_search(query: str):
    """بحث عبر youtube-search-python بدون API"""
    try:
        from program.ytsearch_core import search_youtube_async as _yt_search_async
        results_raw = await _yt_search_async(query, limit=1)
        results = [{"result": [{"title": r["title"], "link": r["url"], "duration": r["duration"], "id": r["id"]}]} for r in results_raw] if results_raw else []
        items = results.get("result", [])
        if not items:
            return None
        item = items[0]
        title = (item.get("title") or query)[:40]
        url = item.get("link") or ""
        duration_raw = item.get("duration") or "0:00"
        thumbs = item.get("thumbnails") or []
        thumbnail = thumbs[-1].get("url") if thumbs else ""
        return title, url, duration_raw, thumbnail
    except Exception as e:
        print(f"[_yt_search error] {e}")
        return None


# ─────────────────────────────────────────
# /song — تحميل أغنية كملف صوتي
# ─────────────────────────────────────────

@Client.on_message(command(["song"]))
async def song(_, message: Message):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply("» **أرسل اسم الأغنية بعد الأمر**\nمثال: /song فيروز")

    m = await message.reply("🎶")
    # استخدم ytdl_utils المركزية لضمان نفس الإعدادات والـ fallback
    from ytdl_utils import audio_opts as _audio_opts
    ydl_ops = _audio_opts("/tmp/%(title)s.%(ext)s")

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
            thumb_data = await asyncio.to_thread(requests.get, thumbnail, allow_redirects=True)
            with open(thumb_name, "wb") as f:
                f.write(thumb_data.content)
    except Exception as e:
        await m.edit("✘ لم يتم العثور على الاغنية\n\nيرجى إعطاء اسم أغنية صالح")
        print(str(e))
        return

    await m.edit("📥 جاري تحميل الملف...")
    try:
        def download_audio():
            with yt_dlp.YoutubeDL(ydl_ops) as ydl:
                info_dict = ydl.extract_info(link, download=True)
                return ydl.prepare_filename(info_dict)

        audio_file = await asyncio.to_thread(download_audio)
        rep = f"**🎧 الرافع @{bn}**"
        secmul, dur, dur_arr = 1, 0, duration.split(":")
        for i in range(len(dur_arr) - 1, -1, -1):
            dur += int(float(dur_arr[i])) * secmul
            secmul *= 60
        await m.edit("📤 جاري رفع الملف...")
        await message.reply_audio(
            audio_file,
            caption=rep,
            thumb=thumb_name,
            parse_mode="md",
            title=title,
            duration=dur,
        )
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
# /vsong /video — تحميل فيديو
# ─────────────────────────────────────────

@Client.on_message(command(["vsong", "video"]))
async def vsong(client, message: Message):
    await message.delete()
    ydl_opts = {
        "format": "bestvideo[height<=720]+bestaudio/best",
        "keepvideo": True,
        "geo_bypass": True,
        "outtmpl": "/tmp/%(title)s.%(ext)s",
        "quiet": True,
        "merge_output_format": "mp4",
        "nocheckcertificate": True,
        "no_warnings": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["tv_embedded", "web", "mweb", "ios"],
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        },
    }

    query = " ".join(message.command[1:])
    if not query:
        return await message.reply("» **أرسل اسم الفيديو بعد الأمر**")

    file_name = None
    preview = None
    try:
        res = await _yt_search(query)
        if not res:
            return await message.reply("✘ **لم يتم العثور على الفيديو**")
        title_v, link, duration_v, thumbnail = res
    except Exception as e:
        return await message.reply(f"✘ **خطأ في البحث:** {e}")

    try:
        msg = await message.reply("📥 **جاري تحميل الفيديو...**")

        def download_video():
            with YoutubeDL(ydl_opts) as ytdl:
                ytdl_data = ytdl.extract_info(link, download=True)
                return ytdl.prepare_filename(ytdl_data), ytdl_data

        file_name, ytdl_data = await asyncio.to_thread(download_video)
    except Exception as e:
        return await msg.edit(f"🚫 **خطأ:** {e}")

    try:
        preview = await asyncio.to_thread(wget.download, thumbnail)
        await msg.edit("📤 **جاري رفع الفيديو...**")
        await message.reply_video(
            file_name,
            duration=int(ytdl_data.get("duration") or 0),
            thumb=preview,
            caption=ytdl_data.get("title", ""),
        )
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


# ─────────────────────────────────────────
# /lyric — كلمات الأغنية
# ─────────────────────────────────────────

@Client.on_message(command(["lyric"]))
async def lyrics(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "» **قم بإرسال اسم الأغنية بعد الأمر**\nمثال: /lyric Fairuz - Ya Ana Ya Ana"
        )
    query = message.text.split(None, 1)[1]
    rep = await message.reply_text("**🎶**")
    try:
        parts = query.split("-", 1)
        if len(parts) == 2:
            artist = parts[0].strip()
            title = parts[1].strip()
        else:
            artist = query.strip()
            title = query.strip()

        url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
        resp = await asyncio.to_thread(requests.get, url, timeout=10)
        data = resp.json()

        if "lyrics" in data and data["lyrics"]:
            lyric_text = data["lyrics"]
            if len(lyric_text) > 4000:
                lyric_text = lyric_text[:4000] + "\n\n... (مقتطع)"
            await rep.edit(f"🎵 **{query}**\n\n{lyric_text}")
        else:
            await rep.edit(
                "✘ **لم يتم العثور على كلمات**\n\n"
                "» جرب الصيغة: /lyric اسم الفنان - اسم الأغنية"
            )
    except Exception as e:
        await rep.edit(
            "✘ **لم يتم العثور على نتائج كلمات غنائية**\n\n"
            "» **يرجى إعطاء اسم أغنية صالح**\n"
            "» مثال: /lyric Fairuz - Nassam Alayna"
        )
        print(e)
