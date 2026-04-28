# play_engine.py — نظام التشغيل المركزي (نمط النسخة القديمة World)
# الفلسفة: نمرر رابط بث مباشر لـ py-tgcalls، بدون تحميل ملف على القرص.
# يدعم: بحث يوتيوب، رابط مباشر، ملف صوتي/صوت مرفق.

import asyncio
import os

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


# ─────────────────────────────────────────
# 1) تنزيل الملف الصوتي (عبر البروكسي) بدلاً من رابط البث المباشر
# ─────────────────────────────────────────
# السبب: لما نستخدم بروكسي، YouTube بيربط الـ stream URL بـ IP البروكسي.
# py-tgcalls/ffmpeg بيفتح الرابط من IP السيرفر مباشرةً (مش عبر البروكسي)،
# فـ YouTube يرفض → الستريم يبقى فاضي → المساعد يدخل الكول صامت.
# الحل: ننزّل الملف بالكامل عبر البروكسي لـ /tmp ثم نمرّر مساره المحلي
# لـ py-tgcalls. كده مفيش طلب يخرج لـ YouTube وقت التشغيل.
# (الملف بيتمسح تلقائياً بعد الأغنية في _do_play على السطر اللي فيه os.remove)

async def get_stream_url(link: str) -> tuple:
    """
    يرجع (1, file_path_local) أو (0, error_msg).
    بنحمّل الملف عبر البروكسي ونرجع مساره المحلي (مش URL).
    """
    from ytdl_utils import download_audio_file
    file_path, err = await asyncio.to_thread(download_audio_file, link)
    if file_path and os.path.exists(file_path):
        return 1, file_path
    return 0, err or "فشل تنزيل الأغنية — حاول لاحقاً"


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
    stream_source: str,   # رابط بث مباشر (URL) أو مسار ملف محلي
    ref_url: str,         # رابط المرجع للعرض
    media_type: str,      # "Audio" أو "YouTube"
    duration,
    thumbnail=None,
    status_msg=None,
):
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
        return

    # ── تشغيل فوري ──
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
        # نظّف ملف محلي لو في
        if isinstance(stream_source, str) and stream_source.startswith("/tmp") and os.path.exists(stream_source):
            try:
                os.remove(stream_source)
            except Exception:
                pass
        await m.reply_text(f"خطأ أثناء التشغيل:\n\n`{e}`")


# ─────────────────────────────────────────
# 6) handler مشترك لكل أوامر التشغيل
# ─────────────────────────────────────────

async def _handle_play(c: Client, m: Message):
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

    # ── حالة 1: ملف صوتي مرفق ──
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

    # ── حالة 2: نص أو رابط ──
    if len(m.command) < 2:
        return await m.reply("» أرسل **اسم أغنية للبحث** أو **ارد على ملف صوتي**")

    query = m.text.split(None, 1)[1].strip()
    suhu = await c.send_message(chat_id, "**🔎 جاري البحث...**")

    from ytdl_utils import extract_video_id, get_video_info
    is_yt_link = bool(extract_video_id(query))

    if is_yt_link:
        info = await asyncio.to_thread(get_video_info, query)
        if not info:
            await suhu.edit("**لم أقدر أقرأ رابط YouTube ده — جرب اسم الأغنية بدل الرابط.**")
            return
        url = info["url"]
        songname = info["title"]
        duration = info["duration"]
        thumbnail = info["thumbnail"]
    else:
        search = await yt_search(query)
        if not search:
            await suhu.edit(f"**لم يتم العثور على نتائج للبحث:**\n`{query}`")
            return
        songname, url, duration, thumbnail = search

    # ✨ نمط النسخة القديمة: نطلع رابط بث مباشر بدل تحميل
    veez, stream_url = await get_stream_url(url)
    if veez == 0:
        await suhu.edit(f"**تعذر تشغيل الأغنية**\n\n» `{stream_url}`")
        return

    await _do_play(
        c, m, chat_id, user_id, songname, stream_url, url,
        "YouTube", duration, thumbnail, suhu,
    )


# ─────────────────────────────────────────
# 7) تسجيل الأوامر
# ─────────────────────────────────────────

@Client.on_message(command(["play", "mplay"]) & other_filters)
async def play_en(c: Client, m: Message):
    await _handle_play(c, m)


@Client.on_message(command2(["تشغيل", "شغل", "تشغيل_موسيقى", "موسيقى"]) & other_filters)
async def play_ar(c: Client, m: Message):
    await _handle_play(c, m)
