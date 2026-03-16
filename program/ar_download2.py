# Copyright (C) 2021 By Amor Music-Project
# Fixed: song() converted to async + await everywhere

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
from driver.filters import command2, other_filters


@Client.on_message(command2(["تحميل", "تحميل_موسيقي"]))
async def song(_, message: Message):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply("» أرسل اسم الأغنية بعد الأمر")
    m = await message.reply("⚡")
    ydl_ops = {"format": "bestaudio/best", "outtmpl": "%(title)s.%(ext)s",
        "proxy": "socks5://127.0.0.1:9050",
        "extractor_args": {"youtube": {"player_client": ["android_vr", "ios", "android"]}}}
    audio_file = None
    thumb_name = None
    try:
        from config import YOUTUBE_API_KEY
        r = await asyncio.to_thread(
            lambda: _ytrequests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={"part": "snippet", "q": query, "type": "video", "maxResults": 1, "key": YOUTUBE_API_KEY},
                timeout=10,
            )
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        if not items:
            await m.edit("✘ لم يتم العثور على الاغنية\n\nيرجى إعطاء اسم أغنية صالح")
            return
        item = items[0]
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"][:40]
        thumbnail = item["snippet"]["thumbnails"].get("high", {}).get("url", "")
        link = f"https://www.youtube.com/watch?v={video_id}"
        r2 = await asyncio.to_thread(
            lambda: _ytrequests.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={"part": "contentDetails", "id": video_id, "key": YOUTUBE_API_KEY},
                timeout=10,
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
        if thumbnail:
            thumb_name = f"{title}.jpg"
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


@Client.on_message(command2(["تحميل_فيديو", "تحميل فيديو"]))
async def vsong(client, message: Message):
    await message.delete()
    ydl_opts = {
        "format": "bestvideo[height<=720]+bestaudio/best",
        "keepvideo": True,
        "geo_bypass": True,
        "outtmpl": "%(title)s.%(ext)s",
        "quiet": True,
        "merge_output_format": "mp4",
        "proxy": "socks5://127.0.0.1:9050",
        "extractor_args": {"youtube": {"player_client": ["android_vr", "ios", "android"]}},
    }
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply("» أرسل اسم الفيديو بعد الأمر")
    file_name = None
    preview = None
    try:
        from config import YOUTUBE_API_KEY
        r = await asyncio.to_thread(
            lambda: _ytrequests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={"part": "snippet", "q": query, "type": "video",
                        "maxResults": 1, "key": YOUTUBE_API_KEY},
                timeout=10,
                proxies={"http": "socks5://127.0.0.1:9050", "https": "socks5://127.0.0.1:9050"},
            )
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        if not items:
            return await message.reply("✘ لم يتم العثور على الفيديو")
        item = items[0]
        video_id = item["id"]["videoId"]
        title_v = item["snippet"]["title"][:40]
        thumbnail = item["snippet"]["thumbnails"].get("high", {}).get("url", "")
        link = f"https://www.youtube.com/watch?v={video_id}"
    except Exception as e:
        return await message.reply(f"✘ خطأ في البحث: {e}")
    try:
        msg = await message.reply("📥 **جاري تحميل الفيديو...**")
        def download_video():
            with YoutubeDL(ydl_opts) as ytdl:
                data = ytdl.extract_info(link, download=True)
                return ytdl.prepare_filename(data), data
        file_name, ytdl_data = await asyncio.to_thread(download_video)
    except Exception as e:
        return await msg.edit(f"🚫 **خطأ:** {e}")
    try:
        if thumbnail:
            preview = await asyncio.to_thread(wget.download, thumbnail)
        await msg.edit("📤 **جاري رفع الفيديو...**")
        await message.reply_video(file_name, duration=int(ytdl_data.get("duration", 0)),
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
    try:
        if len(message.command) < 2:
            return await message.reply_text("» **قم بإرسال اسم الأغنية بعد الأمر**")
        query = message.text.split(None, 1)[1]
        rep = await message.reply_text("⚡")
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
            await rep.edit("✘ **لم يتم العثور على كلمات**\n\n» جرب: /بحث فنان - أغنية")
    except Exception as e:
        await rep.edit("✘ **لم يتم العثور على نتائج**\n\n» مثال: بحث Fairuz - Nassam Alayna")
        print(e)
