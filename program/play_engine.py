# play_engine.py — نظام التشغيل المركزي الجديد
# يستبدل music.py + ar_music.py + ar_music2.py كلها
# يدعم: بحث يوتيوب، رابط مباشر، ملف صوتي، صوت مرفق

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


# ─────────────────────────────────────────
# 1) استخراج رابط التشغيل المباشر من يوتيوب
# ─────────────────────────────────────────

_COOKIES = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cookies.txt")

def _cookies_opt() -> dict:
    if os.path.isfile(_COOKIES) and os.path.getsize(_COOKIES) > 0:
        return {"cookiefile": _COOKIES}
    return {}

def _ydl_base() -> dict:
    opts = {
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "skip_download": True,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 10; K) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
    opts.update(_cookies_opt())
    return opts

_STRATEGIES = [
    {"extractor_args": {"youtube": {"player_client": ["tv_embedded", "ios"]}}},
    {"extractor_args": {"youtube": {"player_client": ["ios"]}},
     "http_headers": {"User-Agent": "com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)"}},
    {"extractor_args": {"youtube": {"player_client": ["android"]}},
     "http_headers": {"User-Agent": "com.google.android.youtube/19.29.37 (Linux; U; Android 14) gzip"}},
    {"extractor_args": {"youtube": {"player_client": ["web_creator"]}}},
    {},  # fallback بدون أي extractor_args
]

def _get_stream_url(link: str) -> tuple:
    """يرجع (1, url) لو نجح، (0, error_msg) لو فشل"""
    base = _ydl_base()
    for strategy in _STRATEGIES:
        opts = {**base, **strategy}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=False)
                # جرب تاخد أفضل رابط صوت مباشر
                fmts = info.get("formats") or []
                audio_fmts = [
                    f for f in fmts
                    if f.get("vcodec") == "none" and f.get("url")
                    and not any(b in f["url"] for b in (".mpd", ".m3u8"))
                ]
                if audio_fmts:
                    audio_fmts.sort(key=lambda f: f.get("abr") or f.get("tbr") or 0, reverse=True)
                    return 1, audio_fmts[0]["url"]
                # fallback: url المباشر من info
                url = info.get("url", "")
                if url and ".mpd" not in url and ".m3u8" not in url:
                    return 1, url
        except Exception as e:
            print(f"[play_engine] strategy failed: {str(e)[:80]}")
    return 0, "فشل استخراج رابط التشغيل — حاول لاحقاً"

async def get_stream_url(link: str) -> tuple:
    return await asyncio.to_thread(_get_stream_url, link)


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
    stream_source: str,   # مسار ملف أو رابط مباشر
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

    # تحقق من الصلاحيات
    err = await _check_bot_perms(c, chat_id)
    if err:
        return await m.reply_text(err)

    # انضمام userbot
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

    # لو كان رابط يوتيوب مباشر
    is_yt_link = "youtube.com/watch" in query or "youtu.be/" in query

    if is_yt_link:
        url = query
        # استخرج عنوان الفيديو بسرعة
        songname = "YouTube Audio"
        duration = "?"
        thumbnail = None
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
                info = ydl.extract_info(url, download=False)
                songname = (info.get("title") or "YouTube Audio")[:70]
                secs = int(info.get("duration") or 0)
                m_, s_ = divmod(secs, 60); h_, m__ = divmod(m_, 60)
                duration = f"{h_}:{m__:02d}:{s_:02d}" if h_ else f"{m__}:{s_:02d}"
                thumbnail = info.get("thumbnail")
        except Exception:
            pass
    else:
        # بحث عادي
        search = await yt_search(query)
        if not search:
            await suhu.edit(f"**لم يتم العثور على نتائج للبحث:**\n`{query}`")
            return
        songname, url, duration, thumbnail = search

    await suhu.edit("**جاري تحضير الصوت...**")
    veez, stream_url = await get_stream_url(url)
    if veez == 0:
        await suhu.edit(f"**مشكلة في تحميل الأغنية**\n\n» `{stream_url}`")
        return

    await _do_play(c, m, chat_id, user_id, songname, stream_url, url, "YouTube", duration, thumbnail, suhu)


# ─────────────────────────────────────────
# 7) تسجيل الأوامر
# ─────────────────────────────────────────

# أوامر إنجليزية
@Client.on_message(command(["play", "mplay"]) & other_filters)
async def play_en(c: Client, m: Message):
    await _handle_play(c, m)


# أوامر عربية
@Client.on_message(command2(["تشغيل", "شغل", "تشغيل_موسيقى", "موسيقى"]) & other_filters)
async def play_ar(c: Client, m: Message):
    await _handle_play(c, m)
