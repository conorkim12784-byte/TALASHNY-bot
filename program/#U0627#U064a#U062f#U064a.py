from pyrogram import Client, filters
from pyrogram.types import Message
from config import BOT_USERNAME
from driver.filters import command2, other_filters, arabic_command
from driver.get_file_id import get_file_id


@Client.on_message((command2(["ايدي", "الايدي"]) | arabic_command(["ايدي", "الايدي"])) & (filters.group | filters.private))
async def showid_ar(_, message: Message):
    await message.delete()
    chat_type = str(message.chat.type)
    if "PRIVATE" in chat_type or "private" in chat_type:
        await message.reply_text(f"<code>{message.chat.id}</code>")
    else:
        _id = "<b>CHAT ID</b>: " + f"<code>{message.chat.id}</code>\n"
        if message.reply_to_message:
            if message.reply_to_message.from_user:
                _id += "<b>USER ID</b>: " + f"<code>{message.reply_to_message.from_user.id}</code>\n"
            file_info = get_file_id(message.reply_to_message)
        else:
            if message.from_user:
                _id += "<b>USER ID</b>: " + f"<code>{message.from_user.id}</code>\n"
            file_info = get_file_id(message)
        if file_info:
            _id += f"<b>{file_info.message_type}</b>: <code>{file_info.file_id}</code>\n"
        await message.reply_text(_id)
