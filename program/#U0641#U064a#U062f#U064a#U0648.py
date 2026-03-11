# Copyright (C) 2021 By Veez Music-Project
# Commit Start Date 20/10/2021
# Finished On 28/10/2021

import re
import asyncio

from config import BOT_USERNAME, IMG_1, IMG_2, IMG_5
from program.utils.inline import stream_markup
from driver.design.thumbnail import thumb
from driver.design.chatname import CHAT_TITLE
from driver.filters import command, other_filters
from driver.filters import command2, other_filters
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
            return result.stderr[:200] if result.stderr else "no output"
        data = json.loads(result.stdout.strip().split("\n")[0])
        songname = data.get("title", "Unknown")
        url = data.get("webpage_url", "")
        duration_secs = data.get("duration", 0)
        mins, secs = divmod(int(duration_secs), 60)
        duration = f"{mins}:{secs:02d}"
        thumbnail = data.get("thumbnail", "")
        return [songname, url, duration, thumbnail]
    except Exception as e:
        print(e)
        return str(e)


async def ytdl(link):
    for fmt in ["best[height<=720]/best", "best[height<=480]/best", "best"]:
        from driver.utils import bash as _bash
        out, err = await _bash(f'yt-dlp -g -f "{fmt}" --no-warnings "{link}"')
        out = out.strip().split("\n")[0].strip() if out else ""
        if out and out.startswith("http"):
            return 1, out
    return 0, err


@Client.on_message(command2(["تشغيل_فيديو","تشغيل فيديو","شغل فيديو","شغل_فيديو","vplay","vp"]) & other_filters)
async def vplay(c: Client, m: Message):
    await m.delete()
    replied = m.reply_to_message
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.sender_chat:
        return await m.reply_text(
            "you're an __Anonymous__ user !\n\n» revert back to your real user account to use this bot."
        )
    try:
        aing = await c.get_me()
    except Exception as e:
        return await m.reply_text(f"error:\n\n{e}")
    a = await c.get_chat_member(chat_id, aing.id)
    if a.status.value not in ("administrator", "creator"):
        await m.reply_text(
            f"💡 لكي تستطيع استخدامي ارفعني **ادمن** مع **صلاحيات**:\n\n» ❌ __حذف الرسائل__\n» ❌ __اضافة المستخدمين__\n» ❌ __ادارة المكالمات المرئية__\n\n **يتم تحديث البوت تلقائي** "
        )
        return
    if not (a.privileges and a.privileges.can_manage_video_chats):
        await m.reply_text(
            "ليس لدي صلاحية:" + "\n\n» ❌ __ادارة المكالمات المرئية__"
        )
        return
    if not a.can_delete_messages:
        await m.reply_text(
            "ليس لدي صلاحية:" + "\n\n» ❌ __حذف الرسائل__"
        )
        return
    if not a.can_invite_users:
        await m.reply_text("ليس لدي صلاحية:" + "\n\n» ❌ __اضافة مستخدمين__")
        return
    try:
        ubot = (await user.get_me()).id
        b = await c.get_chat_member(chat_id, ubot) 
        if b.status.value == "banned":
            await c.unban_chat_member(chat_id, ubot)
            invitelink = await c.export_chat_invite_link(chat_id)
            if invitelink.startswith("https://t.me/+"):
                invitelink = invitelink.replace(
                    "https://t.me/+", "https://t.me/joinchat/"
                )
            await user.join_chat(invitelink)
    except UserNotParticipant:
        try:
            invitelink = await c.export_chat_invite_link(chat_id)
            if invitelink.startswith("https://t.me/+"):
                invitelink = invitelink.replace(
                    "https://t.me/+", "https://t.me/joinchat/"
                )
            await user.join_chat(invitelink)
        except UserAlreadyParticipant:
            pass
        except Exception as e:
            return await m.reply_text(
                f"❌ **فشل المساعد بالانضمام**\n\n**السبب**: `{e}`"
            )

    if replied:
        if replied.video or replied.document:
            loser = await replied.reply("📥 **جاري تحميل الفيديو...**")
            dl = await replied.download()
            link = replied.link
            if len(m.command) < 2:
                Q = 720
            else:
                pq = m.text.split(None, 1)[1]
                if pq == "720" or "480" or "360":
                    Q = int(pq)
                else:
                    Q = 720
                    await loser.edit(
                        "» __فقط 720, 480, 360 مسموح__ \n💡 ** الان يشتغل الفيديو في 720p**"
                    )
            try:
                if replied.video:
                    songname = replied.video.file_name[:70]
                    duration = replied.video.duration
                elif replied.document:
                    songname = replied.document.file_name[:70]
                    duration = replied.document.duration
            except BaseException:
                songname = "Video"

            if chat_id in QUEUE:
                gcname = m.chat.title
                ctitle = await CHAT_TITLE(gcname)
                title = songname
                userid = m.from_user.id
                thumbnail = f"{IMG_5}"
                image = await thumb(thumbnail, title, userid, ctitle)
                pos = add_to_queue(chat_id, songname, dl, link, "Video", Q)
                await loser.delete()
                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                buttons = stream_markup(user_id)
                await m.reply_photo(
                    photo=image,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    caption=f"💡 **تمت إضافة المسار إلى قائمة الانتظار »** `{pos}`\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **المجموعه:** `{chat_id}`\n💡 **الحالة:** `شغال`\n🎧 **طلب بواسطة:** {requester}",
                )
            else:
                gcname = m.chat.title
                ctitle = await CHAT_TITLE(gcname)
                title = songname
                userid = m.from_user.id
                thumbnail = f"{IMG_5}"
                image = await thumb(thumbnail, title, userid, ctitle)
                if Q == 720:
                    amaze = VideoQuality.HD_720p
                elif Q == 480:
                    amaze = VideoQuality.SD_480p
                elif Q == 360:
                    amaze = VideoQuality.SD_360p
                await loser.edit("🔄 **جاري التشغيل انتظر قليلآ...**")
                await call_py.play(
                    chat_id,
                    MediaStream(dl, audio_parameters=AudioQuality.HIGH, video_parameters=amaze),
                )
                add_to_queue(chat_id, songname, dl, link, "Video", Q)
                await loser.delete()
                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                buttons = stream_markup(user_id)
                await m.reply_photo(
                    photo=image,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    caption=f"💡 **بدء تشغيل الفيديو.**\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **المجموعه:** `{chat_id}`\n**⏱ المده:** `{duration}`\n🎧 **طلب بواسطة:** {requester}",
                )
        else:
            if len(m.command) < 2:
                await m.reply(
                    "» الرد على ** ملف فيديو ** أو ** أعط شيئًا للبحث **"
                )
            else:
                loser = await c.send_message(chat_id, "🔎 **جاري البحث انتظر قليلآ...**")
                query = m.text.split(None, 1)[1]
                search = ytsearch(query)
                Q = 720
                amaze = VideoQuality.HD_720p
                if search == 0:
                    await loser.edit("❌ **لم يتم العثور على نتائج**")
                else:
                    songname = search[0]
                    title = search[0]
                    url = search[1]
                    duration = search[2]
                    thumbnail = search[3]
                    userid = m.from_user.id
                    gcname = m.chat.title
                    ctitle = await CHAT_TITLE(gcname)
                    image = await thumb(thumbnail, title, userid, ctitle)
                    veez, ytlink = await ytdl(url)
                    if veez == 0:
                        await loser.edit(f"❌ تم اكتشاف خطأ حاول مجددآ\n\n» `{ytlink}`")
                    else:
                        if chat_id in QUEUE:
                            pos = add_to_queue(
                                chat_id, songname, ytlink, url, "Video", Q
                            )
                            await loser.delete()
                            requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                            buttons = stream_markup(user_id)
                            await m.reply_photo(
                                photo=image,
                                reply_markup=InlineKeyboardMarkup(buttons),
                                caption=f"💡 **تمت إضافة المسار إلى قائمة الانتظار »** `{pos}`\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **المجموعه:** `{chat_id}`\n💡 **الحالة:** `شغال`\n🎧 **طلب بواسطة:** {requester}",
                            )
                        else:
                            try:
                                await loser.edit("🔄 **جاري التشغيل انتظر قليلآ...**")
                                await call_py.play(
                                    chat_id,
                                    MediaStream(ytlink, audio_parameters=AudioQuality.HIGH, video_parameters=amaze),
                                )
                                add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                                await loser.delete()
                                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                                buttons = stream_markup(user_id)
                                await m.reply_photo(
                                    photo=image,
                                    reply_markup=InlineKeyboardMarkup(buttons),
                                    caption=f"💡 **بدء تشغيل الفيديو.**\n\n🏷 **الاسم:** [{songname}]({link})\n💭 **المجموعه:** `{chat_id}`\n⏱️ **المده:** `{duration}`\n🎧 **طلب بواسطة:** {requester}",
                                )
                            except Exception as ep:
                                await loser.delete()
                                await m.reply_text(f"🚫 خطأ: `{ep}`")

    else:
        if len(m.command) < 2:
            await m.reply(
                "» الرد على ** ملف فيديو ** أو ** أعط شيئًا للبحث **"
            )
        else:
            loser = await c.send_message(chat_id, "🔎 **جاري البحث انتظر قليلآ...**")
            query = m.text.split(None, 1)[1]
            search = ytsearch(query)
            Q = 720
            amaze = VideoQuality.HD_720p
            if search == 0:
                await loser.edit("❌ **لم يتم العثور على نتائج**")
            else:
                songname = search[0]
                title = search[0]
                url = search[1]
                duration = search[2]
                thumbnail = search[3]
                userid = m.from_user.id
                gcname = m.chat.title
                ctitle = await CHAT_TITLE(gcname)
                image = await thumb(thumbnail, title, userid, ctitle)
                veez, ytlink = await ytdl(url)
                if veez == 0:
                    await loser.edit(f"❌ تم اكتشاف خطأ حاول مجددآ\n\n» `{ytlink}`")
                else:
                    if chat_id in QUEUE:
                        pos = add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                        await loser.delete()
                        requester = (
                            f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                        )
                        buttons = stream_markup(user_id)
                        await m.reply_photo(
                            photo=image,
                            reply_markup=InlineKeyboardMarkup(buttons),
                            caption=f"💡 **تمت إضافة المسار إلى قائمة الانتظار »** `{pos}`\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **المجموعه:** `{chat_id}`\n💡 **الحالة:** `شغال`\n🎧 **طلب بواسطة:** {requester}",
                        )
                    else:
                        try:
                            await loser.edit("🔄 **جاري التشغيل انتظر قليلآ...**")
                            await call_py.play(
                                chat_id,
                                MediaStream(ytlink, audio_parameters=AudioQuality.HIGH, video_parameters=amaze),
                            )
                            add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                            await loser.delete()
                            requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                            buttons = stream_markup(user_id)
                            await m.reply_photo(
                                photo=image,
                                reply_markup=InlineKeyboardMarkup(buttons),
                                caption=f"💡 **بدء تشغيل الفيديو.**\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **المجموعه:** `{chat_id}`\n**⏱ المده:** `{duration}`\n🎧 **طلب بواسطة:** {requester}",
                            )
                        except Exception as ep:
                            await loser.delete()
                            await m.reply_text(f"🚫 خطأ: `{ep}`")


@Client.on_message(command(["vstream", f"ستريم"]) & other_filters)
async def vstream(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.sender_chat:
        return await m.reply_text(
            "you're an __Anonymous__ user !\n\n» revert back to your real user account to use this bot."
        )
    try:
        aing = await c.get_me()
    except Exception as e:
        return await m.reply_text(f"error:\n\n{e}")
    a = await c.get_chat_member(chat_id, aing.id)
    if a.status.value not in ("administrator", "creator"):
        await m.reply_text(
            f"💡 لكي تستطيع استخدامي ارفعني **ادمن** مع **صلاحيات**:\n\n» ❌ __حذف الرسائل__\n» ❌ __اضافة المستخدمين__\n» ❌ __ادارة المكالمات المرئية__\n\n **يتم تحديث البوت تلقائي** "
        )
        return
    if not (a.privileges and a.privileges.can_manage_video_chats):
        await m.reply_text(
            "ليس لدي صلاحية:" + "\n\n» ❌ __ادارة المكالمات المرئية__"
        )
        return
    if not a.can_delete_messages:
        await m.reply_text(
            "ليس لدي صلاحية:" + "\n\n» ❌ __حذف الرسائل__"
        )
        return
    if not a.can_invite_users:
        await m.reply_text("ليس لدي صلاحية:" + "\n\n» ❌ __اضافة مستخدمين__")
        return
    try:
        ubot = (await user.get_me()).id
        b = await c.get_chat_member(chat_id, ubot)
        if b.status.value == "banned":
            await c.unban_chat_member(chat_id, ubot)
            invitelink = await c.export_chat_invite_link(chat_id)
            if invitelink.startswith("https://t.me/+"):
                invitelink = invitelink.replace(
                    "https://t.me/+", "https://t.me/joinchat/"
                )
            await user.join_chat(invitelink)
    except UserNotParticipant:
        try:
            invitelink = await c.export_chat_invite_link(chat_id)
            if invitelink.startswith("https://t.me/+"):
                invitelink = invitelink.replace(
                    "https://t.me/+", "https://t.me/joinchat/"
                )
            await user.join_chat(invitelink)
        except UserAlreadyParticipant:
            pass
        except Exception as e:
            return await m.reply_text(
                f"❌ **فشل المساعد بالانضمام**\n\n**السبب**: `{e}`"
            )

    if len(m.command) < 2:
        await m.reply("» اعطني رابط مباشر للتشغيل")
    else:
        if len(m.command) == 2:
            link = m.text.split(None, 1)[1]
            Q = 720
            loser = await c.send_message(chat_id, "🔄 **تتم المعالجة انتظر قليلآ...**")
        elif len(m.command) == 3:
            op = m.text.split(None, 1)[1]
            link = op.split(None, 1)[0]
            quality = op.split(None, 1)[1]
            if quality == "720" or "480" or "360":
                Q = int(quality)
            else:
                Q = 720
                await m.reply(
                    "» __فقط 720, 480, 360 مسموح__ \n💡 **الان يشتغل الفيديو في 720p**"
                )
            loser = await c.send_message(chat_id, "🔄 **تتم المعالجة انتظر قليلآ...**")
        else:
            await m.reply("**/vstream {link} {720/480/360}**")

        regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+"
        match = re.match(regex, link)
        if match:
            veez, livelink = await ytdl(link)
        else:
            livelink = link
            veez = 1

        if veez == 0:
            await loser.edit(f"❌ تم اكتشاف خطأ حاول مجددآ\n\n» `{livelink}`")
        else:
            if chat_id in QUEUE:
                pos = add_to_queue(chat_id, "Live Stream", livelink, link, "Video", Q)
                await loser.delete()
                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                buttons = stream_markup(user_id)
                await m.reply_photo(
                    photo=f"{IMG_1}",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    caption=f"💡 **تمت إضافة المسار إلى قائمة الانتظار »** `{pos}`\n\n💭 **المجموعه:** `{chat_id}`\n🎧 **طلب بواسطة:** {requester}",
                )
            else:
                if Q == 720:
                    amaze = VideoQuality.HD_720p
                elif Q == 480:
                    amaze = VideoQuality.SD_480p
                elif Q == 360:
                    amaze = VideoQuality.SD_360p
                try:
                    await loser.edit("🔄 **جاري التشغيل انتظر قليلآ...**")
                    await call_py.play(
                        chat_id,
                        MediaStream(livelink, audio_parameters=AudioQuality.HIGH, video_parameters=amaze),
                    )
                    add_to_queue(chat_id, "Live Stream", livelink, link, "Video", Q)
                    await loser.delete()
                    requester = (
                        f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                    )
                    buttons = stream_markup(user_id)
                    await m.reply_photo(
                        photo=f"{IMG_2}",
                        reply_markup=InlineKeyboardMarkup(buttons),
                        caption=f"💡 **[فيديو مباشر]({link}) بدء التشغيل**\n\n💭 **المجموعه:** `{chat_id}`\n💡 **الحالة:** `شغال`\n🎧 **طلب بواسطة:** {requester}",
                    )
                except Exception as ep:
                    await loser.delete()
                    await m.reply_text(f"🚫 خطأ: `{ep}`")
