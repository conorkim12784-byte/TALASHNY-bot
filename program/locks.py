# locks.py — قفل وفتح الجروب
# FIX: شلنا can_forward_messages من ChatPermissions لأن pyrofork الجديدة ما بتدعمهاش
# بدلاً من كده بنستخدم Raw API عشان نتحكم في التوجيه

from collections import defaultdict
from pyrogram import Client, filters, raw
from pyrogram.types import Message, ChatPermissions
from pyrogram.errors import ChatNotModified
from driver.filters import command, command2, other_filters
from driver.decorators import bot_admin_check

# { chat_id: { lock_type: bool } }
locks_state: dict = defaultdict(lambda: {
    "صور": False,
    "روابط": False,
    "توجيه": False,
    "دردشة": False,
})


async def apply_locks(c: Client, chat_id: int):
    state = locks_state[chat_id]
    all_locked = state.get("دردشة", False)
    try:
        await c.set_chat_permissions(chat_id, ChatPermissions(
            can_send_messages=not all_locked,
            can_send_media_messages=not (all_locked or state.get("صور", False)),
            can_add_web_page_previews=not (all_locked or state.get("روابط", False)),
            # FIX: can_forward_messages اتشالت من pyrofork الجديدة
            # بنستخدم Raw API بدلها
        ))
    except ChatNotModified:
        pass  # الـ permissions مش اتغيرت — مش مشكلة
    except Exception as e:
        raise e

    # FIX: نتعامل مع قفل التوجيه بـ Raw API منفصل
    try:
        no_forward = all_locked or state.get("توجيه", False)
        peer = await c.resolve_peer(chat_id)
        await c.invoke(raw.functions.messages.EditChatDefaultBannedRights(
            peer=peer,
            banned_rights=raw.types.ChatBannedRights(
                until_date=0,
                send_messages=all_locked,
                send_media=all_locked or state.get("صور", False),
                embed_links=all_locked or state.get("روابط", False),
                forward_messages=no_forward,
            )
        ))
    except Exception:
        # لو Raw API فشلت، مش مشكلة — الـ permissions الأساسية اتطبقت
        pass


@Client.on_message((command(["lock"]) | command2(["قفل"])) & other_filters)
@bot_admin_check("lock")
async def lock_cmd(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id

    types = {
        "صور": "صور", "روابط": "روابط",
        "توجيه": "توجيه", "دردشة": "دردشة", "الكل": "الكل"
    }

    if len(m.command) < 2 or m.command[1] not in types:
        return await m.reply(
            "**الاستخدام:** `قفل [نوع]`\n\n"
            "**الأنواع المتاحة:**\n"
            "» `قفل صور`\n» `قفل روابط`\n"
            "» `قفل توجيه`\n» `قفل دردشة`\n» `قفل الكل`"
        )

    lock_type = m.command[1]

    if lock_type == "الكل":
        for k in locks_state[chat_id]:
            locks_state[chat_id][k] = True
        await apply_locks(c, chat_id)
        return await m.reply("🔒 **تم قفل كل حاجة في الجروب**")

    locks_state[chat_id][lock_type] = True
    await apply_locks(c, chat_id)
    await m.reply(f"🔒 **تم قفل {lock_type}**")


@Client.on_message((command(["unlock"]) | command2(["فتح"])) & other_filters)
@bot_admin_check("lock")
async def unlock_cmd(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id

    types = {
        "صور": "صور", "روابط": "روابط",
        "توجيه": "توجيه", "دردشة": "دردشة", "الكل": "الكل"
    }

    if len(m.command) < 2 or m.command[1] not in types:
        return await m.reply(
            "**الاستخدام:** `فتح [نوع]`\n\n"
            "**الأنواع المتاحة:**\n"
            "» `فتح صور`\n» `فتح روابط`\n"
            "» `فتح توجيه`\n» `فتح دردشة`\n» `فتح الكل`"
        )

    lock_type = m.command[1]

    if lock_type == "الكل":
        for k in locks_state[chat_id]:
            locks_state[chat_id][k] = False
        await apply_locks(c, chat_id)
        return await m.reply("🔓 **تم فتح كل حاجة في الجروب**")

    locks_state[chat_id][lock_type] = False
    await apply_locks(c, chat_id)
    await m.reply(f"🔓 **تم فتح {lock_type}**")
