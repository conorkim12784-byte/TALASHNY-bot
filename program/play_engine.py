# play_engine.py — نظام التشغيل المركزي
# يدعم: بحث يوتيوب، رابط مباشر، ملف صوتي، صوت مرفق
# الإصلاح: بيحمّل الأغنية كملف مؤقت بدل streaming مباشر (لأن يوتيوب بيمنعه)

import asyncio
import os

import yt_dlp
from pyrogram import Client
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant, PeerIdInvalid
from pyrogram.types import InlineKeyboardMarkup, Message
from pytgcalls.types import MediaStream, AudioQuality

from config import BOT_USERNAME, IMG_5
from driver.design.chatname import CHAT_TITLE
from driver.design.thumbnail import thumb
from driver.filters import command, command2, other_filters
from driver.queues import QUEUE, add_to_queue
from driver.veez import call_py, user
from program.utils.inline import stream_markup
from program.ytsearch_core import search_youtube_async

# نستخدم callsmusic queues لتتبع الملفات المؤقتة وحذفها تلقائياً
from callsmusic import queues as cs_queues


# ─────────────────────────────────────────
# 1) تحميل الأغنية كملف مؤقت
#    (بدل streaming مباشر — يوتيوب بيرفضه)
# ─────────────────────────────────────────

async def get_stream_url(link: str) -> tuple:
    """
    يحمّل الأغنية كملف مؤقت ويرجع (1, filepath) أو (0, error_msg).
    الملف يُحذف تلقائياً من callsmusic.py بعد انتهاء التشغيل.
    """
    from ytdl_utils import download_audio_file
    path, err = await asyncio.to_thread(download_audio_file, link)
    if path:
        return 1, path
    return 0, err or "فشل تحميل الأغنية — حاول لاحقاً"


# ─────────────────────────────────────────
# 2) بحث يوتيوب
# ─────────────────────────────────────────

async def yt_search(query: str):
    """يرجع [title, url, duration, thumbnail] أو None"""
    results = await search_youtube_async(query, limit=1)
    if not results:
        return None
    r = results[0]
    return [r["title"], r["url"], r["duration"], r["thumbnail"]]


# ─────────────────────────────────────────
# 3) التحقق من صلاحيات البوت في الجروب
# ─────────────────────────────────────────

async def _check_bot_perms(c: Client, chat_id: int) -> str | None:
    """يرجع رسالة خطأ لو في مشكلة، None لو كل شيء تمام"""
    try:
        me = await c.get_me()
        a = await c.get_chat_member(chat_id, me.id)
    except Exception as e:
        return f"خطأ في التحقق من الصلاحيات:\n\n{e}"

    if a.status.value not in ("administrator", "creator"):
        return (
            "لاستخدامي يجب أن أكون **مشرف** مع الصلاحيات:\n\n"
            "» حذف الرسائل\n» دعوة المستخدمين\n» إدارة المكالمات"
        )
    privs = a.privileges
    if not privs:
        return "ليس لدي أي صلاحيات إدارية!"
    if not privs.can_manage_video_chats:
        return "ليس لدي صلاحية:\n\n» إدارة المكالمات المرئية"
    if not privs.can_delete_messages:
        return "ليس لدي صلاحية:\n\n» حذف الرسائل"
    if not privs.can_invite_users:
        return "ليس لدي صلاحية:\n\n» إضافة المستخدمين"
    return None


# ─────────────────────────────────────────
# 4) انضمام الـ userbot للجروب
# ─────────────────────────────────────────

async def _ensure_userbot_joined(c: Client, chat_id: int):
    try:
        ubot_id = (await user.get_me()).id
        member = await c.get_chat_member(chat_id, ubot_id)
        if member.status.value == "banned":
            await c.unban_chat_member(chat_id, ubot_id)
            link = await c.export_chat_invite_link(chat_id)
            link = link.replace("https://t.me/+", "https://t.me/joinchat/")
            await user.join_chat(link)
    except (UserNotParticipant, PeerIdInvalid):
        try:
            link = await c.export_chat_invite_link(chat_id)
            link = link.replace("https://t.me/+", "https://t.me/joinchat/")
            await user.join_chat(link)
        except UserAlreadyParticipant:
            pass
        except Exception as e:
            raise RuntimeError(f"فشل المساعد في الانضمام\n\nالسبب: `{e}`")


# ─────────────────────────────────────────
# 5) تشغيل الأغنية (الـ core الأساسي)
# ─────────────────────────────────────────

async def _do_play(
    c: Client,
    m: Message,
    chat_id: int,
    user_id: int,
    songname: str,
    stream_source: str,   # مسار ملف مؤقت محلي
    ref_url: str,         # رابط المرجع للعرض
    media_type: str,      # "Audio" أو "YouTube"
    duration,
    thumbnail=None,
    status_msg=None,
):
    """يشغل أو يضيف في الطابور — يُستخدم من كل الأوامر"""
    gcname = m.chat.title or ""
    ctitle = await CHAT_TITLE(gcname)
    requester = (m.from_user.first_name or "") if m.from_user else ""

    _thumb_url = None
    if thumbnail and str(thumbnail).startswith(("http://", "https://")):
        _thumb_url = thumbnail
    elif IMG_5 and str(IMG_5).startswith(("http://", "https://")):
        _thumb_url = IMG_5

    # حوّل duration لثواني لو كانت string
    dur_secs = 0
    if isinstance(duration, int):
        dur_secs = duration
    elif isinstance(duration, str) and ":" in duration:
        parts = duration.split(":")
        try:
            if len(parts) == 3:
                dur_secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            else:
                dur_secs = int(parts[0]) * 60 + int(parts[1])
        except Exception:
            dur_secs = 0

    image = await thumb(
        _thumb_url, songname, user_id, ctitle,
        requester=requester, duration=dur_secs
    )
    buttons = stream_markup(user_id)

    # ── في الطابور ──
    if chat_id in QUEUE:
        pos = add_to_queue(chat_id, songname, stream_source, ref_url, media_type, 0)
        # سجّل الملف في cs_queues عشان يُحذف تلقائياً لما يجي دوره
        asyncio.ensure_future(cs_queues.put(
            chat_id, file=stream_source, name=songname, ref=ref_url, type=media_type
        ))
        if status_msg:
            await status_msg.delete()
        await m.reply_photo(
            photo=image,
            reply_markup=InlineKeyboardMarkup(buttons),
            caption=(
                f"**تمت إضافة المقطع إلى قائمة الانتظار »** `{pos}`\n\n"
                f"**الاسم:** [{songname}]({ref_url})\n"
                f"**المدة:** `{duration}`\n"
                f"**طلب بواسطة:** [{requester}](tg://user?id={user_id})"
            ),
        )

    # ── تشغيل فوري ──
    else:
        try:
            if status_msg:
                await status_msg.edit("**يتم التشغيل...**")
            await call_py.play(
                chat_id,
                MediaStream(
                    stream_source,
                    audio_parameters=AudioQuality.HIGH,
                    audio_flags=MediaStream.Flags.AUTO_DETECT,
                    video_flags=MediaStream.Flags.IGNORE,
                ),
            )
            add_to_queue(chat_id, songname, stream_source, ref_url, media_type, 0)
            # سجّل الملف الحالي عشان callsmusic يحذفه لما ينتهي التشغيل
            cs_queues.current_tracks[chat_id] = {"file": stream_source, "name": songname}
            if status_msg:
                await status_msg.delete()
            await m.reply_photo(
                photo=image,
                reply_markup=InlineKeyboardMarkup(buttons),
                caption=(
                    f"**تم تشغيل الموسيقى.**\n\n"
                    f"**الاسم:** [{songname}]({ref_url})\n"
                    f"**المدة:** `{duration}`\n"
                    f"**طلب بواسطة:** [{requester}](tg://user?id={user_id})"
                ),
            )
        except Exception as e:
            if status_msg:
                await status_msg.delete()
            # لو فشل التشغيل امسح الملف المؤقت فوراً
            if stream_source and stream_source.startswith("/tmp") and os.path.exists(stream_source):
                try:
                    os.remove(stream_source)
                except Exception:
                    pass
            await m.reply_text(f"خطأ أثناء التشغيل:\n\n`{e}`")


# ─────────────────────────────────────────
# 6) handler مشترك لكل أوامر التشغيل
# ─────────────────────────────────────────

async def _handle_play(c: Client, m: Message):
    """المنطق المشترك: يدعم ملف مرفق أو نص بحث أو رابط"""
    await m.delete()

    if m.sender_chat:
        return await m.reply_text(
            "أنت مستخدم مجهول الهوية!\n\nارجع لحسابك الأصلي لاستخدام البوت."
        )

    chat_id = m.chat.id
    user_id = m.from_user.id if m.from_user else 0

    err = await _check_bot_perms(c, chat_id)
    if err:
        return await m.reply_text(err)

    try:
        await _ensure_userbot_joined(c, chat_id)
    except RuntimeError as e:
        return await m.reply_text(str(e))

    replied = m.reply_to_message

    # ── حالة 1: ملف صوتي أو رسالة صوتية مرفقة ──
    if replied and (replied.audio or replied.voice):
        suhu = await replied.reply("**جاري تنزيل الصوت...**")
        dl = await replied.download()
        link = replied.link or ""
        try:
            if replied.audio:
                songname = (replied.audio.title or replied.audio.file_name or "Audio")[:70]
                duration = replied.audio.duration or 0
            else:
                songname = "Voice Note"
                duration = replied.voice.duration or 0
        except Exception:
            songname = "Audio"
            duration = 0
        await _do_play(c, m, chat_id, user_id, songname, dl, link, "Audio", duration, status_msg=suhu)
        return

    # ── حالة 2: نص/رابط ──
    if len(m.command) < 2:
        return await m.reply("» أرسل **اسم أغنية للبحث** أو **ارد على ملف صوتي**")

    query = m.text.split(None, 1)[1].strip()
    suhu = await c.send_message(chat_id, "**🎶 جاري البحث...**")

    is_yt_link = "youtube.com/watch" in query or "youtu.be/" in query

    if is_yt_link:
        url = query
        songname = "YouTube Audio"
        duration = "?"
        thumbnail = None
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "nocheckcertificate": True}) as ydl:
                info = ydl.extract_info(url, download=False)
                songname = (info.get("title") or "YouTube Audio")[:70]
                secs = int(info.get("duration") or 0)
                m_, s_ = divmod(secs, 60)
                h_, m__ = divmod(m_, 60)
                duration = f"{h_}:{m__:02d}:{s_:02d}" if h_ else f"{m__}:{s_:02d}"
                thumbnail = info.get("thumbnail")
        except Exception:
            pass
    else:
        search = await yt_search(query)
        if not search:
            await suhu.edit(f"**لم يتم العثور على نتائج للبحث:**\n`{query}`")
            return
        songname, url, duration, thumbnail = search

    await suhu.edit("**📥 جاري تحميل الأغنية...**")
    veez, stream_url = await get_stream_url(url)
    if veez == 0:
        await suhu.edit(f"**مشكلة في تحميل الأغنية**\n\n» `{stream_url}`")
        return

    await suhu.edit("**يتم التشغيل...**")
    await _do_play(c, m, chat_id, user_id, songname, stream_url, url, "YouTube", duration, thumbnail, suhu)


# ─────────────────────────────────────────
# 7) تسجيل الأوامر
# ─────────────────────────────────────────

@Client.on_message(command(["play", "mplay"]) & other_filters)
async def play_en(c: Client, m: Message):
    await _handle_play(c, m)


@Client.on_message(command2(["تشغيل", "شغل", "تشغيل_موسيقى", "موسيقى"]) & other_filters)
async def play_ar(c: Client, m: Message):
    await _handle_play(c, m)
