"""broadcast — مصلَّح: يقبل الأمر العربي والإنجليزي + يستخدم decorator مصلَّح."""
import asyncio
from pyrogram import Client
from pyrogram.types import Message
from driver.veez import user as Anonymous
from driver.filters import command, command2, other_filters
from driver.decorators import sudo_users_only
from config import SUDO_USERS


@Client.on_message(command(["broadcast", "gcast"]) | command2(["اذاعه", "اذاعة", "ذيع"]))
@sudo_users_only
async def broadcast(c: Client, message: Message):
    try:
        await message.delete()
    except Exception:
        pass

    wtf = await message.reply("`جاري بدء الإذاعه...`")
    if not message.reply_to_message and len(message.command) < 2:
        await wtf.edit("**ارد على رساله أو اكتب نصاً مع الأمر**")
        return

    sent = 0
    failed = 0

    if message.reply_to_message:
        text_payload = message.reply_to_message.text or message.reply_to_message.caption or ""
    else:
        text_payload = message.text.split(None, 1)[1]

    async for dialog in Anonymous.iter_dialogs():
        try:
            await Anonymous.send_message(dialog.chat.id, text_payload)
            sent += 1
            if sent % 10 == 0:
                try:
                    await wtf.edit(
                        f"`جاري الإذاعه...`\n\n**تم:** `{sent}`\n**فشل:** `{failed}`"
                    )
                except Exception:
                    pass
            await asyncio.sleep(0.3)
        except Exception:
            failed += 1

    try:
        await wtf.delete()
    except Exception:
        pass
    await message.reply_text(
        f"✅ **تمت الإذاعه**\n\n**تم:** `{sent}` محادثة\n**فشل:** `{failed}` محادثة"
    )
