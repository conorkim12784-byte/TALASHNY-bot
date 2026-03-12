import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from driver.veez import user as Anonymous
from config import SUDO_USERS


@Client.on_message(filters.command(["broadcast", "gcast"]))
async def broadcast(_, message: Message):
    await message.delete()
    if message.from_user.id not in SUDO_USERS:
        return
    wtf = await message.reply("`starting broadcast...`")
    if not message.reply_to_message:
        await wtf.edit("**reply to a message to broadcast**")
        return
    sent = 0
    failed = 0
    lmao = message.reply_to_message.text or message.reply_to_message.caption or ""
    async for dialog in Anonymous.iter_dialogs():
        try:
            await Anonymous.send_message(dialog.chat.id, lmao)
            sent += 1
            await wtf.edit(
                f"`broadcasting...`\n\n**sent:** `{sent}` chats\n**failed:** `{failed}` chats"
            )
            await asyncio.sleep(0.3)
        except Exception:
            failed += 1
    await message.reply_text(
        f"**broadcast done**\n\n**sent:** `{sent}` chats\n**failed:** `{failed}` chats"
    )
