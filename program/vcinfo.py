from driver.decorators import bot_admin_check, all_members_check
# vcinfo.py — مين في الكول + مين مشغّل الأغنية

from pyrogram import Client
from pyrogram.types import Message
from driver.filters import command, command2, other_filters
from driver.queues import QUEUE
from driver.nowplaying import current_requester


# ─────────────────────────────────────────
# أمر: مين في الكول
# ─────────────────────────────────────────
@Client.on_message((command(["incall"]) | command2(["في_الكول", "الكول", "كول", "في الكول", "مين_في_الكول", "مين في الكول"])) & other_filters)
async def who_in_call(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id

    try:
        # نستخدم call_py (PyTgCalls) عبر الـ userbot عشان نجيب المشتركين
        from driver.veez import call_py
        participants = await call_py.get_participants(chat_id)

        if not participants:
            return await m.reply("🎙 **الدردشة الصوتية فارغة حالياً**")

        call_members = []
        for p in participants:
            try:
                uid = p.user_id
                user = await c.get_users(uid)
                if not user.is_bot:
                    name = user.first_name or "مجهول"
                    call_members.append(f"[{name}](tg://user?id={uid})")
            except Exception:
                continue

        if not call_members:
            return await m.reply("🎙 **الدردشة الصوتية فارغة حالياً**")

        members_text = "\n".join(f"  {i+1}. {u}" for i, u in enumerate(call_members))
        await m.reply(
            f"🎙 **المتواجدون في الدردشة الصوتية**\n"
            f"**العدد:** `{len(call_members)}`\n\n"
            f"{members_text}"
        )

    except Exception as e:
        err = str(e).lower()
        if "not found" in err or "empty" in err or "no active" in err or "not active" in err:
            await m.reply("🎙 **لا توجد دردشة صوتية نشطة**")
        else:
            await m.reply(f"❌ **خطأ:** `{e}`")


# ─────────────────────────────────────────
# أمر: مين مشغّل
# ─────────────────────────────────────────
@Client.on_message((command(["nowplaying", "np"]) | command2(["مشغّل", "مشغل", "الان", "مين_مشغل", "مين مشغل"])) & other_filters)
async def now_playing(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id

    if chat_id not in QUEUE or not QUEUE[chat_id]:
        return await m.reply("🎵 **لا يوجد شيء يعزف الآن**")

    current = QUEUE[chat_id][0]
    songname = current[0]
    media_type = current[3]  # Audio أو Video

    # مين طلبها
    requester = current_requester.get(chat_id)
    if requester:
        req_text = f"**طُلبت بواسطة:** [{requester['first_name']}](tg://user?id={requester['user_id']})"
    else:
        req_text = "**طُلبت بواسطة:** `غير معروف`"

    type_icon = "🎬" if media_type == "Video" else "🎵"
    type_text = "فيديو" if media_type == "Video" else "صوت"

    # قايمة الانتظار
    queue_size = len(QUEUE[chat_id])
    queue_text = f"\n📋 **في الانتظار:** `{queue_size - 1}` مقطع" if queue_size > 1 else ""

    await m.reply(
        f"{type_icon} **يعزف الآن**\n\n"
        f"**الاسم:** `{songname}`\n"
        f"**النوع:** `{type_text}`\n"
        f"{req_text}"
        f"{queue_text}"
    )
