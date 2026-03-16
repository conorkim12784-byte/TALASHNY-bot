# ar_youtube.py - بحث YouTube عبر YouTube Data API v3
import asyncio
import re as _re
import requests as _req
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import SUDO_USERS, ASSISTANT_NAME, BOT_USERNAME
from driver.decorators import authorized_users_only, sudo_users_only, errors
from driver.filters import command2, other_filters
from driver.veez import user as USER
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant

TOR_PROXY = "socks5://127.0.0.1:9050"


@Client.on_message(command2(["يوت"]))
async def ytsearch_cmd(_, message: Message):
    await message.delete()
    if len(message.command) < 2:
        return await message.reply_text("/يوت **محتاج كلمة بحث !**")
    query = message.text.split(None, 1)[1]
    m = await message.reply_text("🔎 جاري البحث انتظر قليلآ...")
    try:
        from config import YOUTUBE_API_KEY
        r = await asyncio.to_thread(
            lambda: _req.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={"part": "snippet", "q": query, "type": "video",
                        "maxResults": 5, "key": YOUTUBE_API_KEY},
                timeout=10,
                proxies={"http": TOR_PROXY, "https": TOR_PROXY},
            )
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        if not items:
            return await m.edit("✘ لم يتم العثور على نتائج")

        # جيب مدد الفيديوهات
        ids = ",".join(i["id"]["videoId"] for i in items)
        r2 = await asyncio.to_thread(
            lambda: _req.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={"part": "contentDetails,statistics", "id": ids, "key": YOUTUBE_API_KEY},
                timeout=10,
                proxies={"http": TOR_PROXY, "https": TOR_PROXY},
            )
        )
        r2.raise_for_status()
        details = {d["id"]: d for d in r2.json().get("items", [])}

        text = ""
        for item in items:
            vid_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            channel = item["snippet"]["channelTitle"]
            detail = details.get(vid_id, {})
            iso = detail.get("contentDetails", {}).get("duration", "PT0S")
            mt = _re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
            h, mn, s = (int(mt.group(i) or 0) for i in (1, 2, 3)) if mt else (0, 0, 0)
            total = h * 3600 + mn * 60 + s
            mins, secs = divmod(total, 60)
            duration = f"{mins}:{secs:02d}"
            views = detail.get("statistics", {}).get("viewCount", "0")
            views_fmt = f"{int(views):,}" if views.isdigit() else views
            text += f"🏷 **الاسم:** __{title}__\n"
            text += f"⏱ **المده:** `{duration}`\n"
            text += f"👀 **المشاهدات:** `{views_fmt}`\n"
            text += f"📣 **القناه:** {channel}\n"
            text += f"🔗 **الرابط:** https://www.youtube.com/watch?v={vid_id}\n\n"

        await m.edit(
            text,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🗑 اغلاق", callback_data="cls")]]
            ),
        )
    except Exception as e:
        await m.edit(f"✘ خطأ في البحث: `{e}`")
        print(e)
