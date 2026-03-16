# فيديو.py - اوامر الفيديو العربية فقط (vplay + vstream الانجليزية موجودة في video.py)
import re
import asyncio
from config import BOT_USERNAME, IMG_1, IMG_2, IMG_5
from program.utils.inline import stream_markup
from driver.design.thumbnail import thumb
from driver.design.chatname import CHAT_TITLE
from driver.filters import command2, other_filters
from driver.queues import QUEUE, add_to_queue
from driver.veez import call_py, user
from pyrogram import Client
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, Message
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
import os as _os
from program.video import multisearch_video as _ytsearch_sync

TOR_PROXY = "socks5://127.0.0.1:9050"


import requests as _req
import re as _re2

async def _ytdl_video(link):
    """تحميل فيديو من YouTube محلياً"""
    from program.video import ytdl_video as _yt_vid
    return await _yt_vid(link)

def _get_vq(Q):
    if Q == 480:
        return VideoQuality.SD_480p
    elif Q == 360:
        return VideoQuality.SD_360p
    return VideoQuality.HD_720p


async def _check_and_join(c, m, chat_id):
    try:
        aing = await c.get_me()
    except Exception as e:
        await m.reply_text(f"error:\n\n{e}")
        return False
    a = await c.get_chat_member(chat_id, aing.id)
    if a.status.value not in ("administrator", "creator"):
        await m.reply_text("💡 ارفعني **ادمن** مع صلاحيات:\n\n» ✘ حذف الرسائل\n» ✘ اضافة المستخدمين\n» ✘ ادارة المكالمات")
        return False
    if not (a.privileges and a.privileges.can_manage_video_chats):
        await m.reply_text("ليس لدي صلاحية:\n\n» ✘ ادارة المكالمات المرئية")
        return False
    if not (a.privileges and a.privileges.can_delete_messages):
        await m.reply_text("ليس لدي صلاحية:\n\n» ✘ حذف الرسائل")
        return False
    if not (a.privileges and a.privileges.can_invite_users):
        await m.reply_text("ليس لدي صلاحية:\n\n» ✘ اضافة مستخدمين")
        return False
    try:
        ubot = (await user.get_me()).id
        b = await c.get_chat_member(chat_id, ubot)
        if b.status.value == "banned":
            await c.unban_chat_member(chat_id, ubot)
            invitelink = await c.export_chat_invite_link(chat_id)
            if invitelink.startswith("https://t.me/+"):
                invitelink = invitelink.replace("https://t.me/+", "https://t.me/joinchat/")
            await user.join_chat(invitelink)
    except UserNotParticipant:
        try:
            invitelink = await c.export_chat_invite_link(chat_id)
            if invitelink.startswith("https://t.me/+"):
                invitelink = invitelink.replace("https://t.me/+", "https://t.me/joinchat/")
            await user.join_chat(invitelink)
        except UserAlreadyParticipant:
            pass
        except Exception as e:
            await m.reply_text(f"✘ **فشل المساعد بالانضمام**\n\n**السبب**: `{e}`")
            return False
    return True


@Client.on_message(command2(["فيد", "فيديو"]) & other_filters)
async def vplay_ar(c: Client, m: Message):
    await m.delete()
    replied = m.reply_to_message
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.sender_chat:
        return await m.reply_text("انت مستخدم مجهول!\n\nارجع لحسابك الأصلي لاستخدام البوت.")
    if not await _check_and_join(c, m, chat_id):
        return

    if replied and (replied.video or replied.document):
        loser = await replied.reply("**بـحـث..**")
        dl = await replied.download()
        link = replied.link
        Q = 720
        if len(m.command) >= 2:
            pq = m.text.split(None, 1)[1]
            if pq in ("720", "480", "360"):
                Q = int(pq)
        try:
            if replied.video:
                songname = (replied.video.file_name or "Video")[:70]
                duration = replied.video.duration
            elif replied.document:
                songname = (replied.document.file_name or "Video")[:70]
                duration = 0
        except BaseException:
            songname = "Video"
            duration = 0
        vq = _get_vq(Q)
        gcname = m.chat.title
        ctitle = await CHAT_TITLE(gcname)
        _thumb_url = IMG_5 if IMG_5 and str(IMG_5).startswith(("http://", "https://")) else None
        image = await thumb(_thumb_url, songname, m.from_user.id, ctitle)
        if chat_id in QUEUE:
            pos = add_to_queue(chat_id, songname, dl, link, "Video", Q)
            await loser.delete()
            buttons = stream_markup(user_id)
            await m.reply_photo(
                photo=image, reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"💡 **تمت إضافة المسار إلى قائمة الانتظار »** `{pos}`\n\n🏷 **الاسم:** [{songname}]({link})\n💭 **المجموعه:** `{chat_id}`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
            )
        else:
            await loser.edit("🔄 **جاري التشغيل...**")
            await call_py.play(chat_id, MediaStream(dl, AudioQuality.HIGH, vq))
            add_to_queue(chat_id, songname, dl, link, "Video", Q)
            await loser.delete()
            buttons = stream_markup(user_id)
            await m.reply_photo(
                photo=image, reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"💡 **بدء تشغيل الفيديو.**\n\n🏷 **الاسم:** [{songname}]({link})\n💭 **المجموعه:** `{chat_id}`\n⏱ **المده:** `{duration}`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
            )
    else:
        if len(m.command) < 2:
            await m.reply("» الرد على **ملف فيديو** أو **أعط شيئًا للبحث**")
        else:
            loser = await c.send_message(chat_id, "🎶**")
            query = m.text.split(None, 1)[1]
            search = _ytsearch_sync(query)
            Q = 720
            vq = VideoQuality.HD_720p
            if not search:
                await loser.edit("✘ **لم يتم العثور على نتائج**")
                return
            songname, url, duration, thumbnail = search
            gcname = m.chat.title
            ctitle = await CHAT_TITLE(gcname)
            image = await thumb(thumbnail, songname, m.from_user.id, ctitle)
            veez, ytlink = await _ytdl_video(url)
            if veez == 0:
                await loser.edit(f"✘ تم اكتشاف خطأ حاول مجددآ\n\n» `{ytlink}`")
            elif chat_id in QUEUE:
                pos = add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                await loser.delete()
                buttons = stream_markup(user_id)
                await m.reply_photo(
                    photo=image, reply_markup=InlineKeyboardMarkup(buttons),
                    caption=f"💡 **تمت إضافة المسار إلى قائمة الانتظار »** `{pos}`\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **المجموعه:** `{chat_id}`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
                )
            else:
                try:
                    await loser.edit("🔄 **جاري التشغيل...**")
                    await call_py.play(chat_id, MediaStream(ytlink, AudioQuality.HIGH, vq))
                    add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                    await loser.delete()
                    buttons = stream_markup(user_id)
                    await m.reply_photo(
                        photo=image, reply_markup=InlineKeyboardMarkup(buttons),
                        caption=f"💡 **بدء تشغيل الفيديو.**\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **المجموعه:** `{chat_id}`\n⏱️ **المده:** `{duration}`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
                    )
                except Exception as ep:
                    await loser.delete()
                    await m.reply_text(f"🚫 خطأ: `{ep}`")


@Client.on_message(command2(["ستريم"]) & other_filters)
async def vstream_ar(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.sender_chat:
        return await m.reply_text("انت مستخدم مجهول!\n\nارجع لحسابك الأصلي لاستخدام البوت.")
    if not await _check_and_join(c, m, chat_id):
        return
    if len(m.command) < 2:
        await m.reply("» اعطني رابط مباشر للتشغيل")
        return
    if len(m.command) == 2:
        link = m.text.split(None, 1)[1]
        Q = 720
    elif len(m.command) == 3:
        op = m.text.split(None, 1)[1]
        link = op.split(None, 1)[0]
        quality = op.split(None, 1)[1]
        Q = int(quality) if quality in ("720", "480", "360") else 720
    else:
        await m.reply("**/ستريم {رابط} {720/480/360}**")
        return
    loser = await c.send_message(chat_id, "🔄 **تتم المعالجة...**")
    regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+"
    match = re.match(regex, link)
    if match:
        veez, livelink = await _ytdl_video(link)
    else:
        livelink = link
        veez = 1
    if veez == 0:
        await loser.edit(f"✘ تم اكتشاف خطأ حاول مجددآ\n\n» `{livelink}`")
        return
    vq = _get_vq(Q)
    if chat_id in QUEUE:
        pos = add_to_queue(chat_id, "Live Stream", livelink, link, "Video", Q)
        await loser.delete()
        buttons = stream_markup(user_id)
        await m.reply_photo(
            photo=f"{IMG_1}", reply_markup=InlineKeyboardMarkup(buttons),
            caption=f"💡 **تمت إضافة المسار إلى قائمة الانتظار »** `{pos}`\n\n💭 **المجموعه:** `{chat_id}`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
        )
    else:
        try:
            await loser.edit("🔄 **جاري التشغيل...**")
            await call_py.play(chat_id, MediaStream(livelink, AudioQuality.HIGH, vq))
            add_to_queue(chat_id, "Live Stream", livelink, link, "Video", Q)
            await loser.delete()
            buttons = stream_markup(user_id)
            await m.reply_photo(
                photo=f"{IMG_2}", reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"💡 **[فيديو مباشر]({link}) بدء التشغيل**\n\n💭 **المجموعه:** `{chat_id}`\n💡 **الحالة:** `شغال`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
            )
        except Exception as ep:
            await loser.delete()
            await m.reply_text(f"🚫 خطأ: `{ep}`")
