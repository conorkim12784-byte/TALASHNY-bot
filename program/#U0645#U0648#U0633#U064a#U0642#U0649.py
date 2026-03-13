# موسيقى.py - اوامر التشغيل العربية فقط (play الانجليزي موجود في music.py)
from pyrogram import Client
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, Message
from pytgcalls.types import MediaStream, AudioQuality
from program.utils.inline import stream_markup
from driver.design.thumbnail import thumb
from driver.design.chatname import CHAT_TITLE
from driver.filters import command2, other_filters, arabic_command
from driver.queues import QUEUE, add_to_queue
from driver.veez import call_py, user
from config import BOT_USERNAME, IMG_5
from program.video import ytsearch, ytdl as ytdl


@Client.on_message((command2(["تشغيل", "شغل"]) | arabic_command(["تشغيل", "شغل"])) & other_filters)
async def play_ar(c: Client, m: Message):
    await m.delete()
    replied = m.reply_to_message
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.sender_chat:
        return await m.reply_text("انـت مـسـتـخـدم مـجـهـول\n\nارجـع لـحـسـابـك الاصـلـي لاسـتـخـدام الـبـوت.")
    try:
        aing = await c.get_me()
    except Exception as e:
        return await m.reply_text(f"خـطـا:\n\n{e}")
    a = await c.get_chat_member(chat_id, aing.id)
    if a.status.value not in ("administrator", "creator"):
        await m.reply_text("لاسـتـخـدامـي يـجـب ان اكـون مـشـرف مع الـصـلاحـيـات:\n\n» حـذف الـرسـائـل\n» دعـوة الـمـسـتـخـدمـيـن\n» ادارة الـمـكـالـمـات")
        return
    if not (a.privileges and a.privileges.can_manage_video_chats):
        await m.reply_text("لـيـس لـدي صـلاحـيـة:\n\n» ادارة الـمـكـالـمـات الـمـرئـيـة")
        return
    if not (a.privileges and a.privileges.can_delete_messages):
        await m.reply_text("لـيـس لـدي صـلاحـيـة:\n\n» حـذف الـرسـائـل")
        return
    if not (a.privileges and a.privileges.can_invite_users):
        await m.reply_text("لـيـس لـدي صـلاحـيـة:\n\n» اضـافـة الـمـسـتـخـدمـيـن")
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
            return await m.reply_text(f"**فـشـل الـمـسـاعـد في الانـضـمـام**\n\n**الـسـبـب**: `{e}`")

    if replied and (replied.audio or replied.voice):
        suhu = await replied.reply("**جـاري تـنـزيـل الـصـوت...**")
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
        gcname = m.chat.title
        ctitle = await CHAT_TITLE(gcname)
        image = await thumb(f"{IMG_5}", songname, m.from_user.id, ctitle)
        if chat_id in QUEUE:
            pos = add_to_queue(chat_id, songname, dl, link, "Audio", 0)
            buttons = stream_markup(user_id)
            await suhu.delete()
            await m.reply_photo(
                photo=image, reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"**تـمـت اضـافـة الـمـقـطـع الى قـائـمـة الانـتـظـار »** `{pos}`\n\n**الاسـم:** [{songname}]({link})\n**الـمـجـمـوعـه:** `{chat_id}`\n**الـمـده:** `{duration}`\n**طـلـب بـواسـطـة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})"
            )
        else:
            try:
                await suhu.edit("**يـتـم الـتـشـغـيـل...**")
                await call_py.play(chat_id, MediaStream(dl, AudioQuality.HIGH, video_flags=MediaStream.Flags.IGNORE))
                add_to_queue(chat_id, songname, dl, link, "Audio", 0)
                await suhu.delete()
                buttons = stream_markup(user_id)
                await m.reply_photo(
                    photo=image, reply_markup=InlineKeyboardMarkup(buttons),
                    caption=f"**الاسـم:** [{songname}]({link})\n**الـمـجـمـوعـه:** `{chat_id}`\n**الـمـده:** `{duration}`\n**طـلـب بـواسـطـة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                )
            except Exception as e:
                await suhu.delete()
                await m.reply_text(f"خـطـا:\n\n» {e}")
    else:
        # لو جاي من arabic_command مفيش m.command — نستخدم m.text مباشرة
        parts = m.text.split(None, 1)
        query = parts[1].strip() if len(parts) > 1 else ""
        if not query:
            await m.reply("» عـلـيـك الـرد عـلـى **ملف صوتي** او **اكتب شي للبحث**")
        else:
            suhu = await c.send_message(chat_id, "**جـاري الـبـحـث...**")
            search = ytsearch(query)
            if not isinstance(search, list):
                await suhu.edit(f"**لـم يـتـم الـعـثـور عـلـى نـتـائـج**\n\n`{search}`")
                return
            songname, url, duration, thumbnail = search
            gcname = m.chat.title
            ctitle = await CHAT_TITLE(gcname)
            image = await thumb(thumbnail, songname, m.from_user.id, ctitle)
            veez, ytlink = await ytdl(url)
            if veez == 0:
                await suhu.edit(f"مـشـكـلـة في تـحـمـيـل الاغـنـيـة\n\n» `{ytlink}`")
            elif chat_id in QUEUE:
                pos = add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                await suhu.delete()
                buttons = stream_markup(user_id)
                await m.reply_photo(
                    photo=image, reply_markup=InlineKeyboardMarkup(buttons),
                    caption=f"**تـمـت اضـافـة الـمـقـطـع الى قـائـمـة الانـتـظـار »** `{pos}`\n\n**الاسـم:** [{songname}]({url})\n**الـمـجـمـوعـه:** `{chat_id}`\n**الـمـده:** `{duration}`\n**طـلـب بـواسـطـة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                )
            else:
                try:
                    await suhu.edit("**يـتـم الـتـشـغـيـل...**")
                    await call_py.play(chat_id, MediaStream(ytlink, AudioQuality.HIGH, video_flags=MediaStream.Flags.IGNORE))
                    add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                    await suhu.delete()
                    buttons = stream_markup(user_id)
                    await m.reply_photo(
                        photo=image, reply_markup=InlineKeyboardMarkup(buttons),
                        caption=f"**تـم تـشـغـيـل الـمـوسـيـقـى.**\n\n**الاسـم:** [{songname}]({url})\n**الـمـجـمـوعـه:** `{chat_id}`\n**الـمـده:** `{duration}`\n**طـلـب بـواسـطـة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                    )
                except Exception as ep:
                    await suhu.delete()
                    await m.reply_text(f"خـطـا: `{ep}`")
