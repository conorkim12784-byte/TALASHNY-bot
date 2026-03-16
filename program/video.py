import re
import asyncio
import os
import uuid
import socket

from config import BOT_USERNAME, IMG_1, IMG_2, IMG_5, YOUTUBE_API_KEY
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
import re as _re
import requests as _requests

TOR_PROXY = "socks5://127.0.0.1:9050"
DL_DIR = "/tmp/tgbot_vids"
AUDIO_DIR = "/tmp/tgbot_audio"
os.makedirs(DL_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)


def _is_tor_alive() -> bool:
    """تشيك لو Tor شغال على البورت 9050"""
    try:
        s = socket.create_connection(("127.0.0.1", 9050), timeout=2)
        s.close()
        return True
    except Exception:
        return False


def ytsearch(query: str):
    """بحث عبر YouTube Data API v3"""
    try:
        if not YOUTUBE_API_KEY:
            return None
        proxies = {"http": TOR_PROXY, "https": TOR_PROXY} if _is_tor_alive() else None
        r = _requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={"part": "snippet", "q": query, "type": "video",
                    "maxResults": 1, "key": YOUTUBE_API_KEY},
            timeout=10,
            proxies=proxies,
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        if not items:
            return None
        item = items[0]
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"][:70]
        thumbnail = item["snippet"]["thumbnails"].get("high", {}).get("url", "")
        r2 = _requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"part": "contentDetails", "id": video_id, "key": YOUTUBE_API_KEY},
            timeout=10,
            proxies=proxies,
        )
        r2.raise_for_status()
        detail_items = r2.json().get("items", [])
        iso = detail_items[0]["contentDetails"]["duration"] if detail_items else "PT0S"
        mt = _re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
        h, mn, s = (int(mt.group(i) or 0) for i in (1, 2, 3)) if mt else (0, 0, 0)
        total = h * 3600 + mn * 60 + s
        mins, secs = divmod(total, 60)
        hrs, mins = divmod(mins, 60)
        duration = f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"
        url = f"https://www.youtube.com/watch?v={video_id}"
        return [title, url, duration, thumbnail]
    except Exception as e:
        print(f"[ytsearch error] {e}")
        return f"ERROR: {str(e)[:200]}"


def _clean_env() -> dict:
    """
    بيمسح متغيرات الـ proxy من البيئة عشان yt-dlp ميستخدمش Tor تلقائياً.
    yt-dlp بيقرأ HTTP_PROXY/HTTPS_PROXY من الـ environment — لو Tor مش شغال بيفشل.
    """
    env = os.environ.copy()
    for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
                "ALL_PROXY", "all_proxy", "GLOBAL_AGENT_HTTP_PROXY",
                "GLOBAL_AGENT_HTTPS_PROXY"]:
        env.pop(key, None)
    return env



def _clean_env() -> dict:
    env = os.environ.copy()
    for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
                "ALL_PROXY", "all_proxy", "GLOBAL_AGENT_HTTP_PROXY", "GLOBAL_AGENT_HTTPS_PROXY"]:
        env.pop(key, None)
    return env


def _ydl_get_audio_url(link: str, client: str) -> str | None:
    """yt-dlp Python API - جلب stream URL للصوت"""
    ydl_opts = {
        "quiet": True,
        "js_interpreter": "auto",
        "format": "bestaudio/best",
        "extractor_args": {"youtube": {"player_client": [client]}},
        "skip_download": True,
        "no_warnings": False,
    }
    try:
        import yt_dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            url = info.get("url")
            if not url:
                fmts = info.get("formats") or []
                for f in reversed(fmts):
                    if f.get("url", "").startswith("http"):
                        url = f["url"]
                        break
            return url if url and url.startswith("http") else None
    except Exception as e:
        print(f"[ydl_audio {client}] {e}")
        return None


def _ydl_download_audio(link: str, client: str, out_tpl: str) -> str | None:
    """yt-dlp Python API - تحميل ملف صوتي"""
    ydl_opts = {
        "quiet": True,
        "js_interpreter": "auto",
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "extractor_args": {"youtube": {"player_client": [client]}},
        "outtmpl": out_tpl,
    }
    try:
        import yt_dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        return None
    except Exception as e:
        print(f"[ydl_dl_audio {client}] {e}")
        return str(e)


def _ydl_download_video(link: str, client: str, out_tpl: str, fmt: str) -> str | None:
    """yt-dlp Python API - تحميل فيديو"""
    ydl_opts = {
        "quiet": True,
        "js_interpreter": "auto",
        "format": fmt,
        "extractor_args": {"youtube": {"player_client": [client]}},
        "outtmpl": out_tpl,
        "merge_output_format": "mp4",
    }
    try:
        import yt_dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        return None
    except Exception as e:
        print(f"[ydl_dl_video {client}] {e}")
        return str(e)


async def ytdl_audio(link):
    clients = ["tv_embedded", "ios", "android", "web"]

    # محاولة 1: stream URL مباشر
    for client in clients:
        url = await asyncio.to_thread(_ydl_get_audio_url, link, client)
        if url:
            return 1, url

    # محاولة 2: تحميل ملف محلي
    uid = uuid.uuid4().hex[:8]
    out_tpl = os.path.join(AUDIO_DIR, f"{uid}.%(ext)s")
    last_err = "all clients failed"
    for client in clients:
        last_err = await asyncio.to_thread(_ydl_download_audio, link, client, out_tpl) or "unknown"
        for ff in os.listdir(AUDIO_DIR):
            if ff.startswith(uid):
                return 1, os.path.join(AUDIO_DIR, ff)

    return 0, last_err


ytdl = ytdl_audio


async def ytdl_video(link, quality=720):
    if quality == 480:
        fmt = "bestvideo[height<=480]+bestaudio/best"
    elif quality == 360:
        fmt = "bestvideo[height<=360]+bestaudio/best"
    else:
        fmt = "bestvideo[height<=720]+bestaudio/best"

    uid = uuid.uuid4().hex[:8]
    out_tpl = os.path.join(DL_DIR, f"{uid}.%(ext)s")
    clients = ["tv_embedded", "ios", "android", "web"]
    for client in clients:
        await asyncio.to_thread(_ydl_download_video, link, client, out_tpl, fmt)
        for ff in os.listdir(DL_DIR):
            if ff.startswith(uid):
                return 1, os.path.join(DL_DIR, ff)

    return 0, "failed"


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
    search = ytsearch(query)
    if not search or not isinstance(search, list) or len(search) != 4:
        return await loser.edit(f"✔ **لم يتم العثور على نتائج**\n`{search}`")
    songname, url, duration, thumbnail = search
    await loser.edit("📥 **جاري تنزيل الفيديو...**")
    veez, filepath = await ytdl_video(url, Q)
    if veez == 0:
        return await loser.edit(f"✔ فشل تنزيل الفيديو\n\n» `{filepath[:200]}`")
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
