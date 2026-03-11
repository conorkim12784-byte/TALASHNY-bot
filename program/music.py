# Copyright (C) 2021 By Veez Music-Project

import json
import asyncio

from pyrogram import Client
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, Message
from pytgcalls.types import MediaStream, AudioQuality
from program.utils.inline import stream_markup
from driver.design.thumbnail import thumb
from driver.design.chatname import CHAT_TITLE
from driver.filters import command, other_filters
from driver.queues import QUEUE, add_to_queue
from driver.veez import call_py, user
from driver.utils import bash
from config import BOT_USERNAME, IMG_5


async def ytsearch(query: str):
    try:
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", f"ytsearch1:{query}",
            "--dump-json", "--no-playlist", "--no-download",
            "--no-warnings", "--ignore-errors",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        stdout = stdout.decode("utf-8", errors="ignore").strip()
        stderr = stderr.decode("utf-8", errors="ignore").strip()
        if not stdout:
            return stderr[:200] if stderr else "no output"
        data = json.loads(stdout.split("\n")[0])
        songname = data.get("title", "Unknown")
        url = data.get("webpage_url", "")
        duration_secs = data.get("duration", 0)
        mins, secs = divmod(int(duration_secs), 60)
        duration = f"{mins}:{secs:02d}"
        thumbnail = data.get("thumbnail", "")
        return [songname, url, duration, thumbnail]
    except asyncio.TimeoutError:
        return "timeout"
    except Exception as e:
        return str(e)


async def ytdl(link: str):
    stdout, stderr = await bash(
        f'yt-dlp -g -f "best[height<=?720][width<=?1280]" {link}'
    )
    if stdout:
        return 1, stdout
    return 0, stderr


@Client.on_message(command(["mplay", "play"]) & other_filters)
async def play(c: Client, m: Message):
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
            "لاستخدامي يجب ان اكون **مشرف** مع **الصلاحيات التالية**:\n\n» __حذف الرسائل__\n» __دعوة المستخدمين__\n» __ادارة المكالمات المرئية__"
        )
        return
    if not a.privileges.can_manage_video_chats:
        await m.reply_text("ليس لدي صلاحية:\n\n» __ادارة المكالمات المرئية__")
        return
    if not a.privileges.can_delete_messages:
        await m.reply_text("ليس لدي صلاحية:\n\n» __حذف الرسائل__")
        return
    if not a.privileges.can_invite_users:
        await m.reply_text("ليس لدي صلاحية:\n\n» __اضافة المستخدمين__")
        return
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
            return await m.reply_text(f"**فشل المساعد في الانضمام**\n\n**السبب**: `{e}`")

    if replied and (replied.audio or replied.voice):
        suhu = await replied.reply("**جاري تنزيل الصوت...**")
        dl = await replied.download()
        link = replied.link
        try:
            if replied.audio:
                songname = (replied.audio.title or replied.audio.file_name or "Audio")[:70]
                duration = replied.audio.duration
            elif replied.voice:
                songname = "Voice Note"
                duration = replied.voice.duration
        except BaseException:
            songname = "Audio"
            duration = 0

        if chat_id in QUEUE:
            gcname = m.chat.title
            ctitle = await CHAT_TITLE(gcname)
            image = await thumb(f"{IMG_5}", songname, m.from_user.id, ctitle)
            pos = add_to_queue(chat_id, songname, dl, link, "Audio", 0)
            buttons = stream_markup(user_id)
            await suhu.delete()
            await m.reply_photo(
                photo=image,
                reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"**تمت اضافة المقطع الى قائمة الانتظار »** `{pos}`\n\n**الاسم:** [{songname}]({link})\n**المجموعه:** `{chat_id}`\n**المده:** `{duration}`\n**طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
            )
        else:
            try:
                gcname = m.chat.title
                ctitle = await CHAT_TITLE(gcname)
                image = await thumb(f"{IMG_5}", songname, m.from_user.id, ctitle)
                await suhu.edit("**يتم التشغيل...**")
                await call_py.play(chat_id, MediaStream(dl, AudioQuality.HIGH))
                add_to_queue(chat_id, songname, dl, link, "Audio", 0)
                await suhu.delete()
                buttons = stream_markup(user_id)
                await m.reply_photo(
                    photo=image,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    caption=f"**الاسم:** [{songname}]({link})\n**المجموعه:** `{chat_id}`\n**المده:** `{duration}`\n**طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
                )
            except Exception as e:
                await suhu.delete()
                await m.reply_text(f"خطا:\n\n» {e}")
    else:
        if len(m.command) < 2:
            await m.reply("» عليك الرد على **ملف صوتي** او **اكتب شي للبحث**")
        else:
            suhu = await c.send_message(chat_id, "**جاري البحث...**")
            query = m.text.split(None, 1)[1]
            search = await ytsearch(query)
            if not isinstance(search, list):
                await suhu.edit(f"**لم يتم العثور على نتائج**\n\n`{search}`")
                return
            songname, url, duration, thumbnail = search
            gcname = m.chat.title
            ctitle = await CHAT_TITLE(gcname)
            image = await thumb(thumbnail, songname, m.from_user.id, ctitle)
            veez, ytlink = await ytdl(url)
            if veez == 0:
                await suhu.edit(f"تم اكتشاف مشاكل في yt-dlp\n\n» `{ytlink}`")
            elif chat_id in QUEUE:
                pos = add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                await suhu.delete()
                buttons = stream_markup(user_id)
                await m.reply_photo(
                    photo=image,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    caption=f"**تمت اضافة المقطع الى قائمة الانتظار »** `{pos}`\n\n**الاسم:** [{songname}]({url})\n**المجموعه:** `{chat_id}`\n**المده:** `{duration}`\n**طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
                )
            else:
                try:
                    await suhu.edit("**يتم التشغيل...**")
                    await call_py.play(chat_id, MediaStream(ytlink, AudioQuality.HIGH))
                    add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                    await suhu.delete()
                    buttons = stream_markup(user_id)
                    await m.reply_photo(
                        photo=image,
                        reply_markup=InlineKeyboardMarkup(buttons),
                        caption=f"**تم تشغيل الموسيقى.**\n\n**الاسم:** [{songname}]({url})\n**المجموعه:** `{chat_id}`\n**المده:** `{duration}`\n**طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})",
                    )
                except Exception as ep:
                    await suhu.delete()
                    await m.reply_text(f"خطا: `{ep}`")
