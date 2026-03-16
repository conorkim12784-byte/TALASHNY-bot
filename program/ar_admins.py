from driver.admins import get_administrators, refresh_administrators
# الادمن.py - اوامر الادمن العربية فقط (الانجليزية موجودة في admins.py)
from driver.veez import call_py
from pyrogram import Client
from driver.queues import QUEUE, clear_queue
from driver.filters import command2, other_filters
from driver.decorators import authorized_users_only
from driver.utils import skip_current_song, skip_item
from program.utils.inline import stream_markup
from driver.design.thumbnail import thumb
from driver.design.chatname import CHAT_TITLE
from config import BOT_USERNAME, GROUP_SUPPORT, IMG_5, UPDATES_CHANNEL
from pyrogram.types import InlineKeyboardMarkup, Message, ChatPermissions


@Client.on_message(command2(["اعاده", "تحديث_الادمن", "حدث_الادمن"]) & other_filters)
@authorized_users_only
async def update_admin_ar(client, message):
    await message.delete()
    await refresh_administrators(message.chat)
    await message.reply_text("✔ تم تحديث قائمة المسؤولين بنجاح!")


@Client.on_message(command2(["تخطي"]) & other_filters)
@authorized_users_only
async def skip_ar(c: Client, m: Message):
    await m.delete()
    user_id = m.from_user.id
    chat_id = m.chat.id
    if len(m.command) < 2:
        op = await skip_current_song(chat_id)
        if op == 0:
            await c.send_message(chat_id, "✘ قائمة التشغيل فارغه")
        elif op == 1:
            await c.send_message(chat_id, "✔ قوائم الانتظار **فارغة.**\n\n• خروج المستخدم من الدردشة الصوتية")
        elif op == 2:
            await c.send_message(chat_id, "🗑️ مسح قوائم الانتظار\n\n• مغادرة المستخدم الآلي للدردشة الصوتية")
        else:
            buttons = stream_markup(user_id)
            gcname = m.chat.title
            ctitle = await CHAT_TITLE(gcname)
            image = await thumb(f"{IMG_5}", f"{op[0]}", m.from_user.id, ctitle)
            await c.send_photo(
                chat_id,
                photo=image,
                reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"⏭ **تم التخطي الئ المسار التالي**\n\n🏷 **الاسم:** [{op[0]}]({op[1]})\n💭 **المجموعة:** `{chat_id}`\n💡 **الحالة:** `شغال`\n🎧 **طلب بواسطة:** {m.from_user.mention()}",
            )
    else:
        skip_text = m.text.split(None, 1)[1]
        OP = "🗑 **تمت إزالة الأغنية من قائمة الانتظار:**"
        if chat_id in QUEUE:
            items = [int(x) for x in skip_text.split(" ") if x.isdigit()]
            items.sort(reverse=True)
            for x in items:
                if x != 0:
                    hm = await skip_item(chat_id, x)
                    if hm != 0:
                        OP = OP + "\n" + f"**#{x}** - {hm}"
            await m.reply(OP)


@Client.on_message(command2(["انهاء"]) & other_filters)
@authorized_users_only
async def stop_ar(client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.leave_call(chat_id)
            clear_queue(chat_id)
            await m.reply("✔ **تم ايقاف التشغيل**")
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("✘ **قائمة التشغيل فارغه**")


@Client.on_message(command2(["اسكت"]) & other_filters)
@authorized_users_only
async def skt_ar(client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.leave_call(chat_id)
            clear_queue(chat_id)
            await m.reply("هـسكت بس اوعا تـضرب")
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("مفيش حاجه شغاله عشان اسكت")


@Client.on_message(command2(["ايقاف", "ايقاف_مؤقت", "توقف"]) & other_filters)
@authorized_users_only
async def pause_ar(client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.pause(chat_id)
            await m.reply("⏸ **تم ايقاف المسار موقتآ**\n\n• **لٲستئناف البث استخدم**\n» /resume الامر.")
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("✘ **قائمة التشغيل فارغه**")


@Client.on_message(command2(["كمل", "استكمال", "استكمل"]) & other_filters)
@authorized_users_only
async def resume_ar(client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.resume(chat_id)
            await m.reply("▶️ **تم استئناف المسار**\n\n• **لايقاف البث موقتآ استخدم**\n» /pause الامر")
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("✘ **قائمة التشغيل فارغه**")


@Client.on_message(command2(["ميوت"]) & other_filters)
@authorized_users_only
async def mute_ar(client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.mute(chat_id)
            await m.reply("🔇 **تم كتم الصوت**\n\n• **لرفع الكتم استخدم**\n» /unmute الامر")
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("✘ **قائمة التشغيل فارغه**")


@Client.on_message(command2(["فك_ميوت", "ازاله_ميوت"]) & other_filters)
@authorized_users_only
async def unmute_ar(client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.unmute(chat_id)
            await m.reply("🔊 **تم رفع الكتم**\n\n• **لكتم الصوت استخدم**\n» /mute الامر")
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("✘ **قائمة التشغيل فارغه**")


@Client.on_message(command2(["تحكم", "صوت"]) & other_filters)
@authorized_users_only
async def volume_ar(client, m: Message):
    await m.delete()
    if len(m.command) < 2:
        return await m.reply("**الاستخدام:** تحكم [1-200]")
    vol = m.command[1]
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.change_volume_call(chat_id, volume=int(vol))
            await m.reply(f"✔ **تم ضبط الصوت على** `{vol}`%")
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("✘ **قائمة التشغيل فارغه**")


# ══════════════════════════════════════════════════════════
# أمر: كتم مستخدم (منع الكتابة) — رد على رسالته
# ══════════════════════════════════════════════════════════
@Client.on_message(command2(["كتم", "اسكت_المستخدم", "كتم_مستخدم"]) & other_filters)
@authorized_users_only
async def silence_user(c: Client, m: Message):
    await m.delete()
    replied = m.reply_to_message
    if not replied or not replied.from_user:
        return await m.reply("» **رد على رسالة المستخدم الذي تريد كتمه**")

    target = replied.from_user
    chat_id = m.chat.id

    try:
        await c.restrict_chat_member(
            chat_id,
            target.id,
            ChatPermissions(can_send_messages=False)
        )
        await m.reply(
            f"🔇 **تم كتم المستخدم**\n\n"
            f"👤 **المستخدم:** [{target.first_name}](tg://user?id={target.id})\n"
            f"📋 **السبب:** كتم من قِبل الإدارة\n\n"
            f"» لفك الكتم استخدم أمر **فك كتم** بالرد على رسالته"
        )
    except Exception as e:
        await m.reply(f"✘ **فشل الكتم:** `{e}`")


# ══════════════════════════════════════════════════════════
# أمر: فك كتم مستخدم
# ══════════════════════════════════════════════════════════
@Client.on_message(command2(["فك_كتم", "فك كتم", "رفع_كتم", "رفع كتم"]) & other_filters)
@authorized_users_only
async def unsilence_user(c: Client, m: Message):
    await m.delete()
    replied = m.reply_to_message
    if not replied or not replied.from_user:
        return await m.reply("» **رد على رسالة المستخدم الذي تريد فك كتمه**")

    target = replied.from_user
    chat_id = m.chat.id

    try:
        await c.restrict_chat_member(
            chat_id,
            target.id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_add_web_page_previews=True,
                can_send_polls=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False,
            )
        )
        await m.reply(
            f"🔊 **تم فك كتم المستخدم**\n\n"
            f"👤 **المستخدم:** [{target.first_name}](tg://user?id={target.id})"
        )
    except Exception as e:
        await m.reply(f"✘ **فشل فك الكتم:** `{e}`")
