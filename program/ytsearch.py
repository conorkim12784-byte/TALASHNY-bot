from driver.filters import command
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtube_search import YoutubeSearch
import asyncio
from config import SUDO_USERS, ASSISTANT_NAME, BOT_USERNAME
from driver.decorators import authorized_users_only, sudo_users_only, errors
from driver.filters import command2, other_filters
from driver.veez import user as USER
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant


@Client.on_message(command(["search"]))
async def ytsearch(_, message: Message):
    await message.delete()
    if len(message.command) < 2:
        return await message.reply_text("/search **needs an argument !**")
    query = message.text.split(None, 1)[1]
    m = await message.reply_text("جاري البحث انتظر قليلآ...")
    results = YoutubeSearch(query, max_results=5).to_dict()
    text = ""
    for i in range(5):
        try:
            text += f"🏷 **الاسم:** __{results[i]['title']}__\n"
            text += f"⏱ **المده:** `{results[i]['duration']}`\n"
            text += f"👀 **المشاهدات:** `{results[i]['views']}`\n"
            text += f"📣 **القناه:** {results[i]['channel']}\n"
            text += f"🔗 **الرابط:**: https://www.youtube.com{results[i]['url_suffix']}\n\n"
        except IndexError:
            break
    await m.edit_text(
        text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🗑 اغلاق", callback_data="cls")]]
        ),
    )
    