# ar_youtube.py - بحث عبر SoundCloud و Dailymotion
import asyncio
import yt_dlp
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from driver.filters import command2, other_filters
from pyrogram import Client


def _multi_search(query: str, count: int = 5):
    """بحث على SoundCloud وDailymotion مع بعض"""
    ydl_opts = {
        "quiet": True, "no_warnings": True,
        "extract_flat": True, "skip_download": True,
    }
    results = []
    for source in [f"scsearch{count}", f"dmsearch{count}"]:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"{source}:{query}", download=False)
                entries = info.get("entries") or []
                for item in entries:
                    title = (item.get("title") or "")[:55]
                    url = item.get("url") or item.get("webpage_url") or ""
                    secs = int(item.get("duration") or 0)
                    mins, s = divmod(secs, 60); h, m = divmod(mins, 60)
                    duration = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
                    uploader = item.get("uploader") or item.get("channel") or "—"
                    src_name = "SoundCloud" if "scsearch" in source else "Dailymotion"
                    if url:
                        results.append({
                            "title": title, "url": url,
                            "duration": duration, "uploader": uploader,
                            "source": src_name
                        })
        except Exception as e:
            print(f"[{source} error] {e}")
    return results[:count]


@Client.on_message(command2(["يوت"]))
async def ytsearch_cmd(_, message: Message):
    await message.delete()
    if len(message.command) < 2:
        return await message.reply_text("/يوت **محتاج كلمة بحث !**")
    query = message.text.split(None, 1)[1]
    m = await message.reply_text("🔎 جاري البحث انتظر قليلآ...")
    try:
        items = await asyncio.to_thread(_multi_search, query)
        if not items:
            return await m.edit("✘ لم يتم العثور على نتائج")

        text = ""
        for item in items:
            src_icon = "🎵" if item["source"] == "SoundCloud" else "🎬"
            text += f"{src_icon} **{item['title']}**\n"
            text += f"⏱ `{item['duration']}` | 📣 {item['uploader']} | __{item['source']}__\n"
            text += f"🔗 {item['url']}\n\n"

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
