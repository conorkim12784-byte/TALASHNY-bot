from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import ChatType
from config import BOT_USERNAME
from driver.filters import command2, other_filters
from driver.get_file_id import get_file_id


@Client.on_message(command2(["ايدي","الايدي","id","ID"]))
async def showid(_, message: Message):
    await message.delete()
    chat_type = message.chat.type

    if chat_type == ChatType.PRIVATE:
        user_id = message.chat.id
        await message.reply_text(
            f"<b>ᴀᴄᴄᴏᴜɴᴛ ɪᴅ</b>\n"
            f"<code>{user_id}</code>",
            parse_mode="html"
        )

    elif chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        _id = f"<b>ᴄʜᴀᴛ ɪᴅ</b> : <code>{message.chat.id}</code>\n"
        if message.reply_to_message:
            try:
                _id += f"<b>ᴜsᴇʀ ɪᴅ</b> : <code>{message.reply_to_message.from_user.id}</code>\n"
            except Exception:
                pass
            file_info = get_file_id(message.reply_to_message)
        else:
            _id += f"<b>ᴜsᴇʀ ɪᴅ</b> : <code>{message.from_user.id}</code>\n"
            file_info = get_file_id(message)
        if file_info:
            _id += f"<b>ꜰɪʟᴇ ɪᴅ</b> : <code>{file_info.file_id}</code>\n"
        await message.reply_text(_id, parse_mode="html")
