import re
import asyncio
import os
import uuid

from config import BOT_USERNAME, IMG_1, IMG_2, IMG_5
from program.utils.inline import stream_markup
from driver.design.thumbnail import thumb
from driver.design.chatname import CHAT_TITLE
from driver.filters import command, other_filters, command2
from driver.queues import QUEUE, add_to_queue
from driver.nowplaying import current_requester
from driver.veez import call_py, user
from pyrogram import Client
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, Message
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
import yt_dlp

DL_DIR = "/tmp/tgbot_vids"
AUDIO_DIR = "/tmp/tgbot_audio"
os.makedirs(DL_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)


def _parse_duration(seconds) -> str:
    if not seconds:
        return "0:00"
    seconds = int(seconds)
    mins, secs = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"


def ytsearch(query: str):
    """بحث الصوت — يبدأ بيوتيوب، لو فشل SoundCloud، لو فشل Dailymotion"""
    ydl_opts = {
        "quiet": True, "no_warnings": True,
        "extract_flat": True, "skip_download": True,
    }

    # محاولة 1: YouTube
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            entries = info.get("entries") or []
            if entries:
                item = entries[0]
                title = (item.get("title") or query)[:70]
                url = item.get("url") or item.get("webpage_url") or ""
                secs = int(item.get("duration") or 0)
                mins, s = divmod(secs, 60); h, m = divmod(mins, 60)
                duration = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
                thumbnail = item.get("thumbnail") or ""
                if url:
                    print(f"[ytsearch] YouTube: {title}")
                    return [title, url, duration, thumbnail]
    except Exception as e:
        print(f"[ytsearch YT] {e}")

    # محاولة 2: SoundCloud
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch1:{query}", download=False)
            entries = info.get("entries") or []
            if entries:
                item = entries[0]
                title = (item.get("title") or query)[:70]
                url = item.get("url") or item.get("webpage_url") or ""
                secs = int(item.get("duration") or 0)
                mins, s = divmod(secs, 60); h, m = divmod(mins, 60)
                duration = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
                thumbnail = item.get("thumbnail") or ""
                if url:
                    print(f"[ytsearch] SoundCloud: {title}")
                    return [title, url, duration, thumbnail]
    except Exception as e:
        print(f"[ytsearch SC] {e}")

    # محاولة 3: Dailymotion
    try:
        result = _dm_search(query)
        if result:
            print(f"[ytsearch] Dailymotion: {result[0]}")
            return result
    except Exception as e:
        print(f"[ytsearch DM] {e}")

    return None


def ytsearch_yt(query: str):
    """بحث على YouTube — للفيديو"""
    ydl_opts = {
        "quiet": True, "no_warnings": True,
        "extract_flat": True, "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            entries = info.get("entries") or []
            if not entries:
                return None
            item = entries[0]
            title = (item.get("title") or query)[:70]
            url = item.get("url") or item.get("webpage_url") or ""
            secs = int(item.get("duration") or 0)
            mins, s = divmod(secs, 60); h, m = divmod(mins, 60)
            duration = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
            thumbnail = item.get("thumbnail") or ""
            return [title, url, duration, thumbnail] if url else None
    except Exception as e:
        print(f"[ytsearch_yt error] {e}")
        return None


def _dm_search(query: str):
    """بحث على Dailymotion — مجاني بدون API"""
    ydl_opts = {
        "quiet": True, "no_warnings": True,
        "extract_flat": True, "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"dmsearch1:{query}", download=False)
            entries = info.get("entries") or []
            if not entries:
                return None
            item = entries[0]
            title = (item.get("title") or query)[:70]
            url = item.get("url") or item.get("webpage_url") or ""
            secs = int(item.get("duration") or 0)
            mins, s = divmod(secs, 60); h, m = divmod(mins, 60)
            duration = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
            thumbnail = item.get("thumbnail") or ""
            return [title, url, duration, thumbnail] if url else None
    except Exception as e:
        print(f"[dmsearch error] {e}")
        return None


def _sc_download(link: str, out_tpl: str):
    """تحميل صوت من SoundCloud"""
    ydl_opts = {
        "quiet": True, "no_warnings": True,
        "format": "bestaudio/best", "outtmpl": out_tpl,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        return None
    except Exception as e:
        print(f"[sc_download error] {e}")
        return str(e)


def _yt_download_video(link: str, out_tpl: str, fmt: str) -> str | None:
    """تحميل فيديو — يجرب clients مختلفة بدون cookies"""
    clients = ["tv_embedded", "mweb", "ios", "web_creator", "android"]
    for client in clients:
        ydl_opts = {
            "quiet": True, "no_warnings": True,
            "format": fmt, "outtmpl": out_tpl,
            "merge_output_format": "mp4",
            "extractor_args": {
                "youtube": {
                    "player_client": [client],
                    "player_skip": ["webpage", "js"],
                }
            },
            "socket_timeout": 30,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            return None
        except Exception as e:
            print(f"[yt_dl_video {client}] {e}")
    return "all clients failed"


def _dm_download_video(link: str, out_tpl: str, fmt: str) -> str | None:
    """تحميل فيديو من Dailymotion"""
    ydl_opts = {
        "quiet": True, "no_warnings": True,
        "format": fmt, "outtmpl": out_tpl,
        "merge_output_format": "mp4",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        return None
    except Exception as e:
        print(f"[dm_dl_video error] {e}")
        return str(e)


def _yt_download_audio(link: str, out_tpl: str) -> str | None:
    """تحميل صوت من يوتيوب — بيجرب clients مختلفة بدون cookies"""
    # tv_embedded و mweb بيشتغلوا بدون تحقق في الغالب
    clients = ["tv_embedded", "mweb", "ios", "web_creator", "android"]
    for client in clients:
        ydl_opts = {
            "quiet": True, "no_warnings": True,
            "format": "bestaudio/best",
            "outtmpl": out_tpl,
            "extractor_args": {
                "youtube": {
                    "player_client": [client],
                    "player_skip": ["webpage", "js"],
                }
            },
            "socket_timeout": 30,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            return None
        except Exception as e:
            print(f"[yt_audio {client}] {e}")
    return "all clients failed"


async def ytdl_audio(link):
    """تحميل صوت — يبدأ بيوتيوب، لو فشل يجرب SoundCloud"""
    uid = uuid.uuid4().hex[:8]
    out_tpl = os.path.join(AUDIO_DIR, f"{uid}.%(ext)s")

    # محاولة 1: YouTube صوت فقط
    err = await asyncio.to_thread(_yt_download_audio, link, out_tpl)
    for ff in os.listdir(AUDIO_DIR):
        if ff.startswith(uid):
            print(f"[ytdl_audio] downloaded from YouTube")
            return 1, os.path.join(AUDIO_DIR, ff)

    # محاولة 2: SoundCloud كـ fallback
    sc_uid = uuid.uuid4().hex[:8]
    sc_tpl = os.path.join(AUDIO_DIR, f"{sc_uid}.%(ext)s")
    await asyncio.to_thread(_sc_download, link, sc_tpl)
    for ff in os.listdir(AUDIO_DIR):
        if ff.startswith(sc_uid):
            print(f"[ytdl_audio] downloaded from SoundCloud fallback")
            return 1, os.path.join(AUDIO_DIR, ff)

    return 0, "download failed"


ytdl = ytdl_audio


async def ytdl_video(link, quality=720):
    """
    تحميل فيديو — يجرب YouTube أولاً ثم Dailymotion تلقائياً
    وبيمسح الملف بعد 10 دقائق
    """
    if quality == 480:
        fmt = "bestvideo[height<=480]+bestaudio/best[height<=480]/best"
    elif quality == 360:
        fmt = "bestvideo[height<=360]+bestaudio/best[height<=360]/best"
    else:
        fmt = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"

    uid = uuid.uuid4().hex[:8]
    out_tpl = os.path.join(DL_DIR, f"{uid}.%(ext)s")

    # محاولة 1: YouTube
    await asyncio.to_thread(_yt_download_video, link, out_tpl, fmt)
    for ff in os.listdir(DL_DIR):
        if ff.startswith(uid):
            filepath = os.path.join(DL_DIR, ff)
            asyncio.create_task(_auto_delete(filepath))
            return 1, filepath

    # محاولة 2: Dailymotion لو YouTube فشل
    dm = await asyncio.to_thread(_dm_search, link)
    if dm:
        dm_uid = uuid.uuid4().hex[:8]
        dm_tpl = os.path.join(DL_DIR, f"{dm_uid}.%(ext)s")
        await asyncio.to_thread(_dm_download_video, dm[1], dm_tpl, fmt)
        for ff in os.listdir(DL_DIR):
            if ff.startswith(dm_uid):
                filepath = os.path.join(DL_DIR, ff)
                asyncio.create_task(_auto_delete(filepath))
                return 1, filepath

    return 0, "failed"


async def _auto_delete(filepath: str, delay: int = 600):
    """حذف الملف تلقائياً بعد 10 دقائق"""
    await asyncio.sleep(delay)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass

def multisearch_video(query: str):
    """بحث متعدد المصادر: YouTube أولاً ثم Dailymotion"""
    # YouTube
    result = ytsearch_yt(query)
    if result and isinstance(result, list) and len(result) == 4:
        return result
    # Dailymotion fallback
    result = dmsearch(query)
    if result and isinstance(result, list) and len(result) == 4:
        return result
    return None


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
        await m.reply_text("💡 لكي تستطيع استخدامي ارفعني **ادمن** مع **صلاحيات**:\n\n» ✔ __حذف الرسائل__\n» ✔ __اضافة المستخدمين__\n» ✔ __ادارة المكالمات المرئية__")
        return False
    if not a.privileges.can_manage_video_chats:
        await m.reply_text("ليس لدي صلاحية:\n\n» ✔ __ادارة المكالمات المرئية__")
        return False
    if not a.privileges.can_delete_messages:
        await m.reply_text("ليس لدي صلاحية:\n\n» ✔ __حذف الرسائل__")
        return False
    if not a.privileges.can_invite_users:
        await m.reply_text("ليس لدي صلاحية:\n\n» ✔ __اضافة مستخدمين__")
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
            await m.reply_text(f"✔ **فشل المساعد بالانضمام**\n\n**السبب**: `{e}`")
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
            Q = int(pq) if pq in ("720", "480", "360") else 720
        try:
            songname = (replied.video.file_name or "Video")[:70] if replied.video else (replied.document.file_name or "Video")[:70]
            duration = replied.video.duration if replied.video else 0
        except BaseException:
            songname, duration = "Video", 0
        vq = get_video_quality(Q)
        if chat_id in QUEUE:
            gcname = m.chat.title
            ctitle = await CHAT_TITLE(gcname)
            image = await thumb(f"{IMG_5}", songname, m.from_user.id, ctitle)
            pos = add_to_queue(chat_id, songname, dl, link, "Video", Q)
            current_requester[chat_id] = {"first_name": m.from_user.first_name, "user_id": m.from_user.id}
            await loser.delete()
            buttons = stream_markup(user_id)
            await m.reply_photo(photo=image, reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"💡 **تمت إضافة المسار إلى قائمة الانتظار »** `{pos}`\n\n🏷 **الاسم:** [{songname}]({link})\n💭 **المجموعه:** `{chat_id}`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})")
        else:
            gcname = m.chat.title
            ctitle = await CHAT_TITLE(gcname)
            image = await thumb(f"{IMG_5}", songname, m.from_user.id, ctitle)
            await loser.edit("🔄 **جاري التشغيل...**")
            await call_py.play(chat_id, MediaStream(dl, AudioQuality.HIGH, vq))
            add_to_queue(chat_id, songname, dl, link, "Video", Q)
            current_requester[chat_id] = {"first_name": m.from_user.first_name, "user_id": m.from_user.id}
            await loser.delete()
            buttons = stream_markup(user_id)
            await m.reply_photo(photo=image, reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"💡 **بدء تشغيل الفيديو.**\n\n🏷 **الاسم:** [{songname}]({link})\n💭 **المجموعه:** `{chat_id}`\n**⏱ المده:** `{duration}`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})")
        return

    if len(m.command) < 2:
        return await m.reply("» الرد على **ملف فيديو** أو **أعط شيئًا للبحث**")
    loser = await c.send_message(chat_id, "🔎 **جاري البحث...**")
    query = m.text.split(None, 1)[1]
    Q = 720
    vq = VideoQuality.HD_720p
    search = multisearch_video(query)
    if not search or not isinstance(search, list) or len(search) != 4:
        return await loser.edit("✘ **لم يتم العثور على نتائج على YouTube أو Dailymotion**")
    songname, url, duration, thumbnail = search
    await loser.edit("⏳ **جاري التحميل...**")
    veez, filepath = await ytdl_video(url, Q)
    if veez == 0:
        return await loser.edit(f"✘ **فشل التحميل**\n\n» `{filepath[:200]}`")
    gcname = m.chat.title
    ctitle = await CHAT_TITLE(gcname)
    image = await thumb(thumbnail, songname, m.from_user.id, ctitle)
    if chat_id in QUEUE:
        pos = add_to_queue(chat_id, songname, filepath, url, "Video", Q)
        await loser.delete()
        buttons = stream_markup(user_id)
        await m.reply_photo(photo=image, reply_markup=InlineKeyboardMarkup(buttons),
            caption=f"💡 **تمت إضافة المسار إلى قائمة الانتظار »** `{pos}`\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **المجموعه:** `{chat_id}`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})")
    else:
        try:
            await loser.edit("▶️ **جاري التشغيل...**")
            await call_py.play(chat_id, MediaStream(filepath, AudioQuality.HIGH, vq))
            add_to_queue(chat_id, songname, filepath, url, "Video", Q)
            current_requester[chat_id] = {"first_name": m.from_user.first_name, "user_id": m.from_user.id}
            await loser.delete()
            buttons = stream_markup(user_id)
            await m.reply_photo(photo=image, reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"🎬 **جاري تشغيل الفيديو**\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **المجموعه:** `{chat_id}`\n⏱️ **المده:** `{duration}`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})")
            async def cleanup():
                await asyncio.sleep(600)
                try:
                    os.remove(filepath)
                except Exception:
                    pass
            asyncio.create_task(cleanup())
        except Exception as ep:
            try:
                os.remove(filepath)
            except Exception:
                pass
            await loser.delete()
            await m.reply_text(f"🚫 خطأ: `{ep}`")


@Client.on_message(command(["vstream", "ستريم"]) & other_filters)
async def vstream(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.sender_chat:
        return await m.reply_text("you're an __Anonymous__ user !")
    if not await _check_and_join(c, m, chat_id):
        return
    if len(m.command) < 2:
        return await m.reply("» اعطني رابط مباشر للتشغيل")
    if len(m.command) == 2:
        link = m.text.split(None, 1)[1]
        Q = 720
    elif len(m.command) == 3:
        op = m.text.split(None, 1)[1]
        link = op.split(None, 1)[0]
        quality = op.split(None, 1)[1]
        Q = int(quality) if quality in ("720", "480", "360") else 720
    else:
        return await m.reply("**/vstream {link} {720/480/360}**")
    loser = await c.send_message(chat_id, "🔄 **تتم المعالجة...**")
    regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+"
    match = re.match(regex, link)
    if match:
        veez, livelink = await ytdl_audio(link)
    else:
        livelink = link
        veez = 1
    if veez == 0:
        return await loser.edit(f"✔ تم اكتشاف خطأ\n\n» `{livelink[:200]}`")
    vq = get_video_quality(Q)
    if chat_id in QUEUE:
        pos = add_to_queue(chat_id, "Live Stream", livelink, link, "Video", Q)
        await loser.delete()
        buttons = stream_markup(user_id)
        await m.reply_photo(photo=f"{IMG_1}", reply_markup=InlineKeyboardMarkup(buttons),
            caption=f"💡 **تمت إضافة المسار »** `{pos}`\n\n💭 **المجموعه:** `{chat_id}`")
    else:
        try:
            await loser.edit("🔄 **جاري التشغيل...**")
            await call_py.play(chat_id, MediaStream(livelink, AudioQuality.HIGH, vq))
            add_to_queue(chat_id, "Live Stream", livelink, link, "Video", Q)
            await loser.delete()
            buttons = stream_markup(user_id)
            await m.reply_photo(photo=f"{IMG_2}", reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"💡 **[فيديو مباشر]({link}) بدء التشغيل**\n\n💭 **المجموعه:** `{chat_id}`")
        except Exception as ep:
            await loser.delete()
            await m.reply_text(f"🚫 خطأ: `{ep}`")
