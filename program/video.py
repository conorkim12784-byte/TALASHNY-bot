# Copyright (C) 2021 By Veez Music-Project
# Fixed: ytsearch error handling + unpacking guard

import re
import asyncio

from config import BOT_USERNAME, IMG_1, IMG_2, IMG_5
from program.utils.inline import stream_markup
from driver.design.thumbnail import thumb
from driver.design.chatname import CHAT_TITLE
from driver.filters import command, other_filters, command2
from driver.queues import QUEUE, add_to_queue
from driver.veez import call_py, user
from pyrogram import Client
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, Message
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
import json, subprocess


def ytsearch(query: str):
    try:
        result = subprocess.run(
            ["yt-dlp", f"ytsearch1:{query}", "--dump-json", "--no-playlist", "--no-download",
             "--no-warnings", "--ignore-errors"],
            capture_output=True, text=True, timeout=60
        )
        if not result.stdout.strip():
            print(f"yt-dlp error: {result.stderr[:200]}")
            return None  # FIX: رجّع None بدل string
        data = json.loads(result.stdout.strip().split("\n")[0])
        songname = data.get("title", "Unknown")
        url = data.get("webpage_url", "")
        duration_secs = data.get("duration", 0)
        mins, secs = divmod(int(duration_secs), 60)
        duration = f"{mins}:{secs:02d}"
        thumbnail = data.get("thumbnail", "")
        return [songname, url, duration, thumbnail]  # قائمة بـ 4 عناصر بالظبط
    except Exception as e:
        print(e)
        return None  # FIX: رجّع None بدل str(e)


async def ytdl(link):
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp", "-g", "-f", "best[height<=?720][width<=?1280]", f"{link}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        return 1, stdout.decode().split("\n")[0]
    else:
        return 0, stderr.decode()


def get_video_quality(Q):
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
        await m.reply_text("💡 لكي تستطيع استخدامي ارفعني **ادمن** مع **صلاحيات**:\n\n» ❌ __حذف الرسائل__\n» ❌ __اضافة المستخدمين__\n» ❌ __ادارة المكالمات المرئية__")
        return False
    if not a.privileges.can_manage_video_chats:
        await m.reply_text("ليس لدي صلاحية:\n\n» ❌ __ادارة المكالمات المرئية__")
        return False
    if not a.privileges.can_delete_messages:
        await m.reply_text("ليس لدي صلاحية:\n\n» ❌ __حذف الرسائل__")
        return False
    if not a.privileges.can_invite_users:
        await m.reply_text("ليس لدي صلاحية:\n\n» ❌ __اضافة مستخدمين__")
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
            await m.reply_text(f"❌ **فشل المساعد بالانضمام**\n\n**السبب**: `{e}`")
            return False
    return True


@Client.on_message(command(["vplay"]) & other_filters)
async def vplay(c: Client, m: Message):
    await m.delete()
    replied = m.reply_to_message
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.sender_chat:
        return await m.reply_text("you're an __Anonymous__ user !\n\n» revert back to your real user account to use this bot.")

    if not await _check_and_join(c, m, chat_id):
        return

    if replied and (replied.video or replied.document):
        loser = await replied.reply("📥 **جاري تحميل الفيديو...**")
        dl = await replied.download()
        link = replied.link
        Q = 720
        if len(m.command) >= 2:
            pq = m.text.split(None, 1)[1]
            if pq in ("720", "480", "360"):
                Q = int(pq)
            else:
                await loser.edit("» __فقط 720, 480, 360 مسموح__ \n💡 ** الان يشتغل الفيديو في 720p**")
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

        vq = get_video_quality(Q)
        if chat_id in QUEUE:
            gcname = m.chat.title
            ctitle = await CHAT_TITLE(gcname)
            image = await thumb(f"{IMG_5}", songname, m.from_user.id, ctitle)
            pos = add_to_queue(chat_id, songname, dl, link, "Video", Q)
            await loser.delete()
            buttons = stream_markup(user_id)
            await m.reply_photo(
                photo=image,
                reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"💡 **تمت إضافة المسار إلى قائمة الانتظار »** `{pos}`\n\n🏷 **الاسم:** [{songname}]({link})\n💭 **المجموعه:** `{chat_id}`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
            )
        else:
            gcname = m.chat.title
            ctitle = await CHAT_TITLE(gcname)
            image = await thumb(f"{IMG_5}", songname, m.from_user.id, ctitle)
            await loser.edit("🔄 **جاري التشغيل انتظر قليلآ...**")
            await call_py.play(chat_id, MediaStream(dl, AudioQuality.HIGH, vq))
            add_to_queue(chat_id, songname, dl, link, "Video", Q)
            await loser.delete()
            buttons = stream_markup(user_id)
            await m.reply_photo(
                photo=image,
                reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"💡 **بدء تشغيل الفيديو.**\n\n🏷 **الاسم:** [{songname}]({link})\n💭 **المجموعه:** `{chat_id}`\n**⏱ المده:** `{duration}`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
            )
    else:
        if len(m.command) < 2:
            await m.reply("» الرد على **ملف فيديو** أو **أعط شيئًا للبحث**")
        else:
            loser = await c.send_message(chat_id, "🔎 **جاري البحث انتظر قليلآ...**")
            query = m.text.split(None, 1)[1]
            search = ytsearch(query)
            Q = 720
            vq = VideoQuality.HD_720p

            # FIX: كان بيقارن بـ 0 بس الفانكشن بترجع None أو list
            if not search or not isinstance(search, list) or len(search) != 4:
                await loser.edit("❌ **لم يتم العثور على نتائج**")
                return

            songname, url, duration, thumbnail = search  # آمن دلوقتي
            gcname = m.chat.title
            ctitle = await CHAT_TITLE(gcname)
            image = await thumb(thumbnail, songname, m.from_user.id, ctitle)
            veez, ytlink = await ytdl(url)
            if veez == 0:
                await loser.edit(f"❌ تم اكتشاف خطأ حاول مجددآ\n\n» `{ytlink}`")
            elif chat_id in QUEUE:
                pos = add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                await loser.delete()
                buttons = stream_markup(user_id)
                await m.reply_photo(
                    photo=image,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    caption=f"💡 **تمت إضافة المسار إلى قائمة الانتظار »** `{pos}`\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **المجموعه:** `{chat_id}`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
                )
            else:
                try:
                    await loser.edit("🔄 **جاري التشغيل انتظر قليلآ...**")
                    await call_py.play(chat_id, MediaStream(ytlink, AudioQuality.HIGH, vq))
                    add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                    await loser.delete()
                    buttons = stream_markup(user_id)
                    await m.reply_photo(
                        photo=image,
                        reply_markup=InlineKeyboardMarkup(buttons),
                        caption=f"💡 **بدء تشغيل الفيديو.**\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **المجموعه:** `{chat_id}`\n⏱️ **المده:** `{duration}`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
                    )
                except Exception as ep:
                    await loser.delete()
                    await m.reply_text(f"🚫 خطأ: `{ep}`")


@Client.on_message(command(["vstream", "ستريم"]) & other_filters)
async def vstream(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.sender_chat:
        return await m.reply_text("you're an __Anonymous__ user !\n\n» revert back to your real user account to use this bot.")

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
        await m.reply("**/vstream {link} {720/480/360}**")
        return

    loser = await c.send_message(chat_id, "🔄 **تتم المعالجة انتظر قليلآ...**")
    regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+"
    match = re.match(regex, link)
    if match:
        veez, livelink = await ytdl(link)
    else:
        livelink = link
        veez = 1

    if veez == 0:
        await loser.edit(f"❌ تم اكتشاف خطأ حاول مجددآ\n\n» `{livelink}`")
        return

    vq = get_video_quality(Q)
    if chat_id in QUEUE:
        pos = add_to_queue(chat_id, "Live Stream", livelink, link, "Video", Q)
        await loser.delete()
        buttons = stream_markup(user_id)
        await m.reply_photo(
            photo=f"{IMG_1}",
            reply_markup=InlineKeyboardMarkup(buttons),
            caption=f"💡 **تمت إضافة المسار إلى قائمة الانتظار »** `{pos}`\n\n💭 **المجموعه:** `{chat_id}`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
        )
    else:
        try:
            await loser.edit("🔄 **جاري التشغيل انتظر قليلآ...**")
            await call_py.play(chat_id, MediaStream(livelink, AudioQuality.HIGH, vq))
            add_to_queue(chat_id, "Live Stream", livelink, link, "Video", Q)
            await loser.delete()
            buttons = stream_markup(user_id)
            await m.reply_photo(
                photo=f"{IMG_2}",
                reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"💡 **[فيديو مباشر]({link}) بدء التشغيل**\n\n💭 **المجموعه:** `{chat_id}`\n💡 **الحالة:** `شغال`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
            )
        except Exception as ep:
            await loser.delete()
            await m.reply_text(f"🚫 خطأ: `{ep}`")
