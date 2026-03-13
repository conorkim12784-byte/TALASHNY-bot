# الادمن.py - اوامر الادمن العربية فقط (الانجليزية موجودة في admins.py)
from cache.admins import admins
from driver.veez import call_py
from pyrogram import Client
from pyrogram.enums import ChatMembersFilter
from driver.queues import QUEUE, clear_queue
from driver.filters import command2, other_filters, arabic_command, get_query
from driver.decorators import authorized_users_only
from driver.utils import skip_current_song, skip_item
from program.utils.inline import stream_markup
from driver.design.thumbnail import thumb
from driver.design.chatname import CHAT_TITLE
from config import BOT_USERNAME, GROUP_SUPPORT, IMG_5, UPDATES_CHANNEL
from pyrogram.types import InlineKeyboardMarkup, Message


@Client.on_message((command2(["اعاده", "تحديث_الادمن", "حدث_الادمن"]) | arabic_command(["اعاده", "تحديث_الادمن", "حدث_الادمن"])) & other_filters)
@authorized_users_only
async def update_admin_ar(client, message):
    await message.delete()
    global admins
    new_admins = []
    new_ads = client.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS)
    async for u in new_ads:
        new_admins.append(u.user.id)
    admins[message.chat.id] = new_admins
    await message.reply_text("✅ تم إعادة تحميل البوت بشكل صحيح!\n✅ تم تحديث قائمة المسؤولين!")


@Client.on_message((command2(["تخطي"]) | arabic_command(["تخطي"])) & other_filters)
@authorized_users_only
async def skip_ar(c: Client, m: Message):
    await m.delete()
    user_id = m.from_user.id
    chat_id = m.chat.id
    if not (m.command and len(m.command) >= 2) and not (m.text and " " in m.text.strip()):
        op = await skip_current_song(chat_id)
        if op == 0:
            await c.send_message(chat_id, "❌ قائمة التشغيل فارغه")
        elif op == 1:
            await c.send_message(chat_id, "✅ قوائم الانتظار **فارغة.**\n\n• خروج المستخدم من الدردشة الصوتية")
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


@Client.on_message((command2(["انهاء"]) | arabic_command(["انهاء"])) & other_filters)
@authorized_users_only
async def stop_ar(client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.leave_call(chat_id)
            clear_queue(chat_id)
            await m.reply("✅ **تم ايقاف التشغيل**")
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("❌ **قائمة التشغيل فارغه**")


@Client.on_message((command2(["اسكت"]) | arabic_command(["اسكت"])) & other_filters)
@authorized_users_only
async def skt_ar(client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.leave_call(chat_id)
            clear_queue(chat_id)
            await m.reply("حاضر هسكت اهو 🥲")
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("مفيش حاجه شغاله عشان اسكت")


@Client.on_message((command2(["ايقاف", "ايقاف_مؤقت", "توقف"]) | arabic_command(["ايقاف", "ايقاف_مؤقت", "توقف"])) & other_filters)
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
        await m.reply("❌ **قائمة التشغيل فارغه**")


@Client.on_message((command2(["كمل", "استكمال", "استكمل"]) | arabic_command(["كمل", "استكمال", "استكمل"])) & other_filters)
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
        await m.reply("❌ **قائمة التشغيل فارغه**")


@Client.on_message((command2(["ميوت"]) | arabic_command(["ميوت"])) & other_filters)
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
        await m.reply("❌ **قائمة التشغيل فارغه**")


@Client.on_message((command2(["فك_ميوت", "ازاله_ميوت"]) | arabic_command(["فك_ميوت", "ازاله_ميوت"])) & other_filters)
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
        await m.reply("❌ **قائمة التشغيل فارغه**")


@Client.on_message((command2(["تحكم", "صوت"]) | arabic_command(["تحكم", "صوت"])) & other_filters)
@authorized_users_only
async def volume_ar(client, m: Message):
    await m.delete()
    vol = get_query(m, ["تحكم", "صوت"])
    if not vol:
        return await m.reply("**الاستخدام:** تحكم [1-200]")
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.change_volume_call(chat_id, volume=int(vol))
            await m.reply(f"✅ **تم ضبط الصوت على** `{vol}`%")
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("❌ **قائمة التشغيل فارغه**")
