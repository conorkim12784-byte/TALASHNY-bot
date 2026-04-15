# ytsearch.py — بحث YouTube بدون API أو proxy

import asyncio
from pyrogram import Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from driver.filters import command, other_filters


@Client.on_message(command(["search"]))
async def ytsearch(_, message: Message):
    await message.delete()
    if len(message.command) < 2:
        return await message.reply_text("/search **needs an argument !**")
    query = message.text.split(None, 1)[1]
    m = await message.reply_text("🔎 جاري البحث انتظر قليلآ...")
    try:
        from youtubesearchpython import VideosSearch
        results = await asyncio.to_thread(lambda: VideosSearch(query, limit=5).result())
        items = results.get("result", [])
        if not items:
            return await m.edit("✘ لم يتم العثور على نتائج")

        text = ""
        for item in items:
            vid_id = item.get("id") or item.get("link", "").split("v=")[-1].split("&")[0]
            title = item.get("title", "")
            channel = (item.get("channel") or {}).get("name", "")
            duration = item.get("duration") or "0:00"
            views_raw = (item.get("viewCount") or {}).get("text") or item.get("viewCount") or "0"
            if isinstance(views_raw, str):
                views_fmt = views_raw
            else:
                views_fmt = f"{int(views_raw):,}"
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
