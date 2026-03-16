# Copyright (C) 2021 By Amor Music-Project
# Fixed: YoutubeSearch استبدلناها بـ yt-dlp مباشرة عشان youtube_search بايظة

from __future__ import unicode_literals
import asyncio
import json
import os
import subprocess
import requests
import wget
import yt_dlp
from pyrogram import Client
from pyrogram.types import Message
from yt_dlp import YoutubeDL
from config import BOT_USERNAME as bn
from driver.filters import command2, other_filters

COOKIES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cookies.txt")
TOR_PROXY = "socks5://127.0.0.1:9050"


def _parse_iso_duration(iso: str) -> int:
    import re as _re
    match = _re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not match:
        return 0
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    return h * 3600 + m * 60 + s


def _ytsearch(query: str):
    """بحث عبر YouTube Data API v3 — مش بيتحجب"""
    try:
        from config import YOUTUBE_API_KEY
        if not YOUTUBE_API_KEY:
            print("[ytsearch] YOUTUBE_API_KEY غير موجود في .env")
            return None
        search_url = "https://www.googleapis.com/youtube/v3/search"
        r = requests.get(search_url, params={
            "part": "snippet", "q": query, "type": "video",
            "maxResults": 1, "key": YOUTUBE_API_KEY,
        }, timeout=10, proxies={"http": TOR_PROXY, "https": TOR_PROXY})
        r.raise_for_status()
        items = r.json().get("items", [])
        if not items:
            return None
        item = items[0]
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"][:40]
        thumbnail = item["snippet"]["thumbnails"].get("high", {}).get("url", "")
        r2 = requests.get("https://www.googleapis.com/youtube/v3/videos", params={
            "part": "contentDetails", "id": video_id, "key": YOUTUBE_API_KEY,
        }, timeout=10, proxies={"http": TOR_PROXY, "https": TOR_PROXY})
        r2.raise_for_status()
        detail_items = r2.json().get("items", [])
        iso = detail_items[0]["contentDetails"]["duration"] if detail_items else "PT0S"
        duration_secs = _parse_iso_duration(iso)
        url = f"https://www.youtube.com/watch?v={video_id}"
        return title, url, duration_secs, thumbnail
    except Exception as e:
        print(f"[ytsearch error] {e}")
        return None


@Client.on_message(command2(["تحميل", "تحميل_موسيقي"]))
async def song(_, message: Message):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply("» أرسل اسم الأغنية بعد الأمر")
    m = await message.reply("🔎 جاري البحث انتظر قليلآ...")
    ydl_ops = {
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "outtmpl": "%(title)s.%(ext)s",
        "quiet": True,
        "geo_bypass": True,
        "proxy": TOR_PROXY,
        "extractor_args": {"youtube": {"player_client": ["android", "ios", "web"]}},
    }
    if os.path.exists(COOKIES_FILE):
        ydl_ops["cookiefile"] = COOKIES_FILE

    audio_file = None
    thumb_name = None
    try:
        search = await asyncio.to_thread(_ytsearch, query)
        if not search:
            return await m.edit("✘ لم يتم العثور على الاغنية\n\nيرجى إعطاء اسم أغنية صالح")
        title, link, duration_secs, thumbnail = search
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
        if audio_file and not os.path.exists(audio_file):
            base = os.path.splitext(audio_file)[0]
            audio_file = base + ".mp3"
        rep = f"**🎧 الرافع @{bn}**"
        await m.edit("📤 جاري رفع الملف...")
        await message.reply_audio(audio_file, caption=rep, thumb=thumb_name,
                                   parse_mode="md", title=title, duration=duration_secs)
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
        "proxy": TOR_PROXY,
        "extractor_args": {"youtube": {"player_client": ["android", "ios", "web"]}},
    }
    if os.path.exists(COOKIES_FILE):
        ydl_opts["cookiefile"] = COOKIES_FILE

    query = " ".join(message.command[1:])
    if not query:
        return await message.reply("» أرسل اسم الفيديو بعد الأمر")
    file_name = None
    preview = None
    try:
        search = await asyncio.to_thread(_ytsearch, query)
        if not search:
            return await message.reply("✘ لم يتم العثور على الفيديو")
        title, link, duration_secs, thumbnail = search
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
        await message.reply_video(file_name, duration=duration_secs,
                                   thumb=preview, caption=title)
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
        rep = await message.reply_text("🔎 **جاري البحث عن كلمات...**")
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
