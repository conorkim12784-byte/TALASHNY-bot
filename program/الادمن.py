from cache.admins import admins
from driver.veez import call_py, bot
from pyrogram import Client
from pyrogram.enums import ChatMembersFilter, filters
from driver.design.thumbnail import thumb
from driver.design.chatname import CHAT_TITLE
from driver.queues import QUEUE, clear_queue
from driver.filters import command2, other_filters
from driver.decorators import authorized_users_only
from driver.utils import skip_current_song, skip_item
from program.utils.inline import (
    stream_markup,
    close_mark,
    back_mark,
)
from config import BOT_USERNAME, GROUP_SUPPORT, IMG_5, UPDATES_CHANNEL
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)


@Client.on_message(command2(["اعاده","تحديث_الادمن","حدث_الادمن"]) & other_filters)
@authorized_users_only
async def update_admin(client, message):
    await message.delete()
    global admins
    new_admins = []
    new_ads = client.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS)
    async for u in new_ads:
        new_admins.append(u.user.id)
    admins[message.chat.id] = new_admins
    await message.reply_text(
        "✅تم إعادة تحميل البوت ** بشكل صحيح! **  \n✅ ** تم تحديث قائمة المسؤولين ** **! ** "
    )

@Client.on_message(command2(["تخطي"]) & other_filters)
@authorized_users_only
async def skip(c: Client, m: Message):
    await m.delete()
    user_id = m.from_user.id
    chat_id = m.chat.id
    if len(m.command) < 2:
        op = await skip_current_song(chat_id)
        if op == 0:
            await c.send_message(chat_id, "❌ قائمة التشغيل فارغه")
        elif op == 1:
            await c.send_message(chat_id, "✅ قوائم الانتظار ** فارغة. ** \n\n** • خروج المستخدم من الدردشة الصوتية ** ")
        elif op == 2:
            await c.send_message(chat_id, "🗑️مسح قوائم الانتظار ** \n \n ** • مغادرة المستخدم الآلي للدردشة الصوتية ** ")
        else:
            buttons = stream_markup(user_id)
            requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
            thumbnail = f"{IMG_5}"
            title = f"{op[0]}"
            userid = m.from_user.id
            gcname = m.chat.title
            ctitle = await CHAT_TITLE(gcname)
            image = await thumb(thumbnail, title, userid, ctitle)
            await c.send_photo(
                chat_id,
                photo=image,
                reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"⏭ **تم التخطي الئ المسار التالي**\n\n🏷 **الاسم:** [{op[0]}]({op[1]})\n💭 **المجموعة:** `{chat_id}`\n💡 **الحالة:** `شغال`\n🎧 **طلب بواسطة:** {m.from_user.mention()}",
            )
    else:
        skip = m.text.split(None, 1)[1]
        OP = "🗑 **تمت إزالة الأغنية من قائمة الانتظار:**"
        if chat_id in QUEUE:
            items = [int(x) for x in skip.split(" ") if x.isdigit()]
            items.sort(reverse=True)
            for x in items:
                if x == 0:
                    pass
                else:
                    hm = await skip_item(chat_id, x)
                    if hm == 0:
                        pass
                    else:
                        OP = OP + "\n" + f"**#{x}** - {hm}"
            await m.reply(OP)

@Client.on_message(
    command2(["انهاء"])
    & other_filters
)
@authorized_users_only
async def stop(client, m: Message):
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
        
@Client.on_message(
    command2(["اسكت"])
    & other_filters
)
@authorized_users_only
async def stop(client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.leave_call(chat_id)
            clear_queue(chat_id)
            await m.reply("حاضر هسكت اهو🥲")
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("مفيش حاجه شغاله عشان اسكت")

@Client.on_message(
    command2(["ايقاف","ايقاف_مؤقت","توقف"]) & other_filters
)
@authorized_users_only
async def pause(client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.pause(chat_id)
            await m.reply(
                "⏸ **تم ايقاف المسار موقتآ**\n\n• **لٲستئناف البث استخدم**\n» /resume الامر."
            )
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("❌ **قائمة التشغيل فارغه**")

@Client.on_message(
    command2(["كمل","استكمال","استكمل"]) & other_filters
)
@authorized_users_only
async def resume(client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.resume(chat_id)
            await m.reply(
                "▶️ **تم استئناف المسار**\n\n• **لايقاف البث موقتآ استخدم**\n» /pause الامر"
            )
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("❌ **قائمة التشغيل فارغه**")


@Client.on_message(
    command2(["ميوت"]) & other_filters
)
@authorized_users_only
async def mute(client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.mute(chat_id)
            await m.reply(
                "🔇 **تم كتم الصوت**\n\n• **لرفع الكتم استخدم**\n» /unmute الامر" 
            )
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("❌ **قائمة التشغيل فارغه**")

@Client.on_message(
    command2(["فك_ميوت","حذف_الميوت","حذف الميوت","فك ميوت","ازاله ميوت","ازاله_ميوت"]) & other_filters
)
@authorized_users_only
async def unmute(client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.unmute(chat_id)
            await m.reply(
                "🔊 **تم رفع الكتم**\n\n• **لكتم الصوت استخدم**\n» /mute الامر"
            )
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("❌ **قائمة التشغيل فارغه**")

@Client.on_message(
    command2(["تحكم","صوت"]) & other_filters
)
@authorized_users_only
async def change_volume(client, m: Message):
    range = m.command[1]
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.change_volume_call(chat_id, volume=int(range))
            await m.reply(
                f"✅ **تم ضبط الصوت على** `{range}`%"
            )
        except Exception as e:
            await m.reply(f"🚫 **خطأ:**\n\n`{e}`")
    else:
        await m.reply("❌ **قائمة التشغيل فارغه**")
