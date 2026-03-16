# ar_youtube.py - بحث عبر yt-dlp (SoundCloud + YouTube)
import asyncio
import yt_dlp
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from driver.filters import command2, other_filters
from pyrogram import Client

def _search_results(query: str):
    """بحث على SoundCloud بـ 5 نتائج"""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch5:{query}", download=False)
            return info.get("entries") or []
    except Exception as e:
        print(f"[ar_youtube search error] {e}")
        return []


@Client.on_message(command2(["يوت"]))
async def ytsearch_cmd(_, message: Message):
    await message.delete()
    if len(message.command) < 2:
        return await message.reply_text("/يوت **محتاج كلمة بحث !**")
    query = message.text.split(None, 1)[1]
    m = await message.reply_text("🔎 جاري البحث انتظر قليلآ...")
    try:
        items = await asyncio.to_thread(_search_results, query)
        if not items:
            return await m.edit("✘ لم يتم العثور على نتائج")

        text = ""
        for item in items:
            title = (item.get("title") or "")[:60]
            url = item.get("url") or item.get("webpage_url") or ""
            secs = int(item.get("duration") or 0)
            mins, s = divmod(secs, 60)
            h, mn = divmod(mins, 60)
            duration = f"{h}:{mn:02d}:{s:02d}" if h else f"{mn}:{s:02d}"
            uploader = item.get("uploader") or item.get("channel") or ""
            text += f"🏷 **الاسم:** __{title}__\n"
            text += f"⏱ **المده:** `{duration}`\n"
            text += f"📣 **الفنان:** {uploader}\n"
            text += f"🔗 **الرابط:** {url}\n\n"

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
