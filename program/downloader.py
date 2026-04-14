# Copyright (C) 2021 By Amor Music-Project
# Fixed: song() converted to async, lyric API replaced, cleanup improved
# FIX: أضفنا cookies لـ yt_dlp عشان YouTube بيطلب authentication

from __future__ import unicode_literals

import asyncio
import os

import requests
import wget
import yt_dlp
from pyrogram import Client
from pyrogram.types import Message
import requests as _ytrequests
import re as _ytre
from yt_dlp import YoutubeDL

from config import BOT_USERNAME as bn
from driver.decorators import humanbytes
from driver.filters import command, other_filters

# FIX: مسار الـ cookies
TOR_PROXY = "socks5://127.0.0.1:9050"
COOKIES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cookies.txt")


# ─────────────────────────────────────────
# /song  — تحميل أغنية كملف صوتي
# ─────────────────────────────────────────

async def _yt_api_search(query):
    """بحث عبر YouTube Data API v3"""
    from config import YOUTUBE_API_KEY
    import asyncio
    r = await asyncio.to_thread(
        lambda: _ytrequests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={"part": "snippet", "q": query, "type": "video", "maxResults": 1, "key": YOUTUBE_API_KEY},
            timeout=10,
            proxies={"http": TOR_PROXY, "https": TOR_PROXY},
        )
    )
    r.raise_for_status()
    items = r.json().get("items", [])
    if not items:
        return None
    item = items[0]
    video_id = item["id"]["videoId"]
    title = item["snippet"]["title"][:40]
    thumbnail = item["snippet"]["thumbnails"].get("high", {}).get("url", "")
    r2 = await asyncio.to_thread(
        lambda: _ytrequests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"part": "contentDetails", "id": video_id, "key": YOUTUBE_API_KEY},
            timeout=10,
            proxies={"http": TOR_PROXY, "https": TOR_PROXY},
        )
    )
    r2.raise_for_status()
    detail_items = r2.json().get("items", [])
    iso = detail_items[0]["contentDetails"]["duration"] if detail_items else "PT0S"
    mt = _ytre.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    h, mn, s = (int(mt.group(i) or 0) for i in (1, 2, 3)) if mt else (0, 0, 0)
    total_s = h * 3600 + mn * 60 + s
    _m, _s = divmod(total_s, 60)
    _h, _m = divmod(_m, 60)
    duration = f"{_h}:{_m:02d}:{_s:02d}" if _h else f"{_m}:{_s:02d}"
    link = f"https://www.youtube.com/watch?v={video_id}"
    return title, link, duration, thumbnail

@Client.on_message(command(["song"]))
async def song(_, message: Message):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply("» **أرسل اسم الأغنية بعد الأمر**\nمثال: /song فيروز")

    m = await message.reply("🎶")
    ydl_ops = {
        "format": "bestaudio/best",
        "outtmpl": "/tmp/%(title)s.%(ext)s",
        "cookiefile": COOKIES_FILE,
        "extractor_args": {"youtube": {"player_client": ["ios", "android", "tv_embedded"]}},
    }

    audio_file = None
    thumb_name = None

    try:
        res = await _yt_api_search(query)
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
        "cookiefile": COOKIES_FILE,
        "extractor_args": {"youtube": {"player_client": ["ios", "android", "tv_embedded"]}},
    }

    query = " ".join(message.command[1:])
    if not query:
        return await message.reply("» **أرسل اسم الفيديو بعد الأمر**")

    file_name = None
    preview = None
    try:
        res = await _yt_api_search(query)
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
            duration=int(ytdl_data["duration"]),
            thumb=preview,
            caption=ytdl_data["title"],
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
            title  = parts[1].strip()
        else:
            artist = query.strip()
            title  = query.strip()

        url  = f"https://api.lyrics.ovh/v1/{artist}/{title}"
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
