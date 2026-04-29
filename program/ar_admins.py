from driver.admins import get_administrators, refresh_administrators
# الادمن.py - اوامر الادمن العربية فقط (الانجليزية موجودة في admins.py)
import re
from driver.veez import call_py
from pyrogram import Client
from driver.queues import QUEUE, clear_queue
from driver.filters import command2, other_filters
from driver.decorators import authorized_users_only, admin_only, owner_only, target_rank_check
from driver.utils import skip_current_song, skip_item
from program.utils.inline import stream_markup
from program.utils.progress_bar import stop_progress, start_progress, hide_buttons
from driver.design.thumbnail import thumb
from driver.design.chatname import CHAT_TITLE
from config import BOT_USERNAME, GROUP_SUPPORT, IMG_5, UPDATES_CHANNEL
from pyrogram.types import InlineKeyboardMarkup, Message, ChatPermissions


def _yt_thumb_from_link(link: str) -> str:
    """نطلع رابط صورة الأغنية من لينك يوتيوب — لو فشل نرجع IMG_5"""
    if not link or not isinstance(link, str):
        return IMG_5
    m = re.search(r"(?:v=|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})", link)
    if m:
        vid = m.group(1)
        return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    return IMG_5


@Client.on_message(command2(["اعاده", "تحديث_الادمن", "حدث_الادمن"]) & other_filters)
@owner_only
async def update_admin_ar(client, message):
    await message.delete()
    await refresh_administrators(message.chat)
    await message.reply_text("✔ تم تحديث قائمة المسؤولين بنجاح!")


@Client.on_message(command2(["تخطي"]) & other_filters)
@admin_only
async def skip_ar(c: Client, m: Message):
    await m.delete()
    user_id = m.from_user.id
    chat_id = m.chat.id
    if len(m.command) < 2:
        # نخفي أزرار الأغنية الحالية قبل ما نشغل التالي
        await hide_buttons(chat_id)
        op = await skip_current_song(chat_id)
        if op == 0:
            # القائمة فارغة — رسالة بس بدون إنهاء التشغيل
            await c.send_message(chat_id, "✘ **قائمة التشغيل فارغه** — مفيش مقطع تالي للتخطي إليه")
        elif op == 2:
            await c.send_message(chat_id, "🗑️ مسح قوائم الانتظار\n\n• مغادرة المستخدم الآلي للدردشة الصوتية")
        else:
            buttons = stream_markup(user_id)
            gcname = m.chat.title or ""
            ctitle = await CHAT_TITLE(gcname)
            requester = m.from_user.first_name or ""
            # نجيب صورة الأغنية الجديدة من لينك يوتيوب
            song_thumb_url = _yt_thumb_from_link(op[1])
            # المدة لو موجودة من القائمة (عنصر رقم 3 في الإرجاع)
            duration = op[3] if len(op) > 3 else 0
            dur_secs = duration if isinstance(duration, int) else 0
            image = await thumb(
                song_thumb_url, f"{op[0]}", m.from_user.id, ctitle,
                requester=requester, duration=dur_secs,
            )
            sent = await c.send_photo(
                chat_id,
                photo=image,
                reply_markup=InlineKeyboardMarkup(buttons),
                caption=(
                    f"**تم تشغيل الموسيقى.**\n\n"
                    f"**الاسم:** [{op[0]}]({op[1]})\n"
                    f"**المدة:** `{duration if duration else 'غير معروف'}`\n"
                    f"**طلب بواسطة:** [{requester}](tg://user?id={user_id})"
                ),
            )
            # شغّل شريط التقدم للأغنية الجديدة بمدتها الحقيقية
            try:
                await start_progress(c, chat_id, sent, dur_secs, user_id)
            except Exception as e:
                print(f"[skip start_progress error] {e}")
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
@admin_only
async def stop_ar(client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.leave_call(chat_id)
            clear_queue(chat_id)
            await hide_buttons(chat_id)
            await m.reply("✔ **تم ايقاف التشغيل**")
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("✘ **قائمة التشغيل فارغه**")


@Client.on_message(command2(["اسكت"]) & other_filters)
@admin_only
async def skt_ar(client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.leave_call(chat_id)
            clear_queue(chat_id)
            stop_progress(chat_id)
            await m.reply("هـسكت بس اوعا تـضرب")
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("مفيش حاجه شغاله عشان اسكت")


@Client.on_message(command2(["ايقاف", "ايقاف_مؤقت", "توقف"]) & other_filters)
@admin_only
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
@admin_only
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
@admin_only
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
@admin_only
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
@admin_only
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
# أمر: كتم مستخدم
# ══════════════════════════════════════════════════════════
@Client.on_message(command2(["كتم", "اسكت_المستخدم", "كتم_مستخدم"]) & other_filters)
@admin_only
@target_rank_check
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
@admin_only
@target_rank_check
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
