import asyncio
from pyrogram import Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from driver.filters import command
from program.ytsearch_core import search_youtube_async


@Client.on_message(command(["search"]))
async def ytsearch_cmd(_, message: Message):
    await message.delete()
    if len(message.command) < 2:
        return await message.reply_text("/search **needs an argument !**")
    query = message.text.split(None, 1)[1]
    m = await message.reply_text("🔎 جاري البحث انتظر قليلآ...")
    try:
        items = await search_youtube_async(query, limit=5)
        if not items:
            return await m.edit("✘ لم يتم العثور على نتائج")
        text = ""
        for item in items:
            text += f"🏷 **الاسم:** __{item['title']}__\n"
            text += f"⏱ **المده:** `{item['duration']}`\n"
            text += f"👀 **المشاهدات:** `{item['views']}`\n"
            text += f"📣 **القناه:** {item['channel']}\n"
            text += f"🔗 **الرابط:** {item['url']}\n\n"
        await m.edit(
            text,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🗑 اغلاق", callback_data="cls")]]),
        )
    except Exception as e:
        await m.edit(f"✘ خطأ في البحث: `{e}`")
        print(e)
