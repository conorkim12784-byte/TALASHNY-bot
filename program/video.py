# Copyright (C) 2021 By Veez Music-Project
# /play  → تحميل صوت مؤقت وتشغيله (أكثر استقراراً من streaming مباشر)
# /vplay → تنزيل الفيديو محلياً، تشغيله، مسحه بعد الانتهاء

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
import json, subprocess, requests as _requests
from config import YOUTUBE_API_KEY

COOKIES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cookies.txt")
TOR_PROXY = "socks5://127.0.0.1:9050"
DL_DIR = "/tmp/tgbot_vids"
AUDIO_DIR = "/tmp/tgbot_audio"
os.makedirs(DL_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)


def _parse_iso_duration(iso: str) -> str:
    """تحويل PT3M45S لـ 3:45"""
    import re
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not match:
        return "0:00"
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    total = h * 3600 + m * 60 + s
    mins, secs = divmod(total, 60)
    hrs, mins = divmod(mins, 60)
    if hrs:
        return f"{hrs}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def ytsearch(query: str):
    """
    بحث عبر YouTube Data API v3 — مش بيتحجب
    بترجع: [title, url, duration, thumbnail]  أو  None لو فشل
    """
    try:
        if not YOUTUBE_API_KEY:
            print("[ytsearch] YOUTUBE_API_KEY غير موجود في .env")
            return None

        # خطوة 1: ابحث عن الفيديو وجيب الـ video_id
        search_url = "https://www.googleapis.com/youtube/v3/search"
        search_params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 1,
            "key": YOUTUBE_API_KEY,
        }
        r = _requests.get(search_url, params=search_params, timeout=10,
                          proxies={"http": TOR_PROXY, "https": TOR_PROXY})
        r.raise_for_status()
        items = r.json().get("items", [])
        if not items:
            return None

        item = items[0]
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"][:70]
        thumbnail = item["snippet"]["thumbnails"].get("high", {}).get("url", "")

        # خطوة 2: جيب مدة الفيديو
        details_url = "https://www.googleapis.com/youtube/v3/videos"
        details_params = {
            "part": "contentDetails",
            "id": video_id,
            "key": YOUTUBE_API_KEY,
        }
        r2 = _requests.get(details_url, params=details_params, timeout=10,
                           proxies={"http": TOR_PROXY, "https": TOR_PROXY})
        r2.raise_for_status()
        detail_items = r2.json().get("items", [])
        iso_duration = detail_items[0]["contentDetails"]["duration"] if detail_items else "PT0S"
        duration = _parse_iso_duration(iso_duration)

        url = f"https://www.youtube.com/watch?v={video_id}"
        return [title, url, duration, thumbnail]

    except Exception as e:
        err = str(e)
        print(f"[ytsearch error] {err}")
        return f"ERROR: {err[:200]}"


async def _run_ytdlp(cmd):
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode().strip(), stderr.decode()


async def ytdl_audio(link):
    """
    تحميل الصوت كملف مؤقت — بدون تحويل ffmpeg.
    بترجع: (1, filepath) لو نجح  أو  (0, error) لو فشل
    """
    uid = uuid.uuid4().hex[:8]
    out_tpl = os.path.join(AUDIO_DIR, f"{uid}.%(ext)s")

    clients = [
        ("android",    False),
        ("android_vr", False),
        ("ios",        False),
        ("mweb",       False),
        ("web",        True),
    ]
    last_err = ""
    for client, use_cookies in clients:
        cmd = [
            "yt-dlp", "--no-playlist",
            "--extractor-args", f"youtube:player_client={client}",
            "-f", "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
            "--proxy", TOR_PROXY,
            "-o", out_tpl,
        ]
        if use_cookies and os.path.exists(COOKIES_FILE):
            cmd += ["--cookies", COOKIES_FILE]
        cmd.append(link)
        _, last_err = await _run_ytdlp(cmd)
        for ff in os.listdir(AUDIO_DIR):
            if ff.startswith(uid):
                return 1, os.path.join(AUDIO_DIR, ff)

    # محاولة أخيرة بدون تحديد client
    cmd = [
        "yt-dlp", "--no-playlist",
        "-f", "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "--proxy", TOR_PROXY,
        "-o", out_tpl,
    ]
    if os.path.exists(COOKIES_FILE):
        cmd += ["--cookies", COOKIES_FILE]
    cmd.append(link)
    await _run_ytdlp(cmd)
    for ff in os.listdir(AUDIO_DIR):
        if ff.startswith(uid):
            return 1, os.path.join(AUDIO_DIR, ff)

    return 0, last_err


# alias للـ music.py و ar_music.py
ytdl = ytdl_audio


async def ytdl_video(link, quality=720):
    """
    تنزيل فيديو.
    """
    uid = uuid.uuid4().hex[:8]
    out_tpl = os.path.join(DL_DIR, f"{uid}.%(ext)s")

    if quality == 480:
        fmt = "bestvideo[height<=480]+bestaudio/best[height<=480]/bestvideo[height<=480]/best"
    elif quality == 360:
        fmt = "bestvideo[height<=360]+bestaudio/best[height<=360]/bestvideo[height<=360]/best"
    else:
        fmt = "bestvideo[height<=720]+bestaudio/best[height<=720]/bestvideo[height<=720]/best"

    clients = [
        ("android",    False),
        ("android_vr", False),
        ("ios",        False),
        ("mweb",       False),
        ("web",        True),
    ]
    last_err = ""
    for client, use_cookies in clients:
        cmd = ["yt-dlp", "--no-playlist",
               "--extractor-args", f"youtube:player_client={client}",
               "-f", fmt, "--proxy", TOR_PROXY,
               "-o", out_tpl, "--merge-output-format", "mp4"]
        if use_cookies and os.path.exists(COOKIES_FILE):
            cmd += ["--cookies", COOKIES_FILE]
        cmd.append(link)
        _, last_err = await _run_ytdlp(cmd)
        for ff in os.listdir(DL_DIR):
            if ff.startswith(uid):
                return 1, os.path.join(DL_DIR, ff)

    cmd = ["yt-dlp", "--no-playlist", "-f", fmt, "--proxy", TOR_PROXY,
           "-o", out_tpl, "--merge-output-format", "mp4"]
    if os.path.exists(COOKIES_FILE):
        cmd += ["--cookies", COOKIES_FILE]
    cmd.append(link)
    await _run_ytdlp(cmd)
    for ff in os.listdir(DL_DIR):
        if ff.startswith(uid):
            return 1, os.path.join(DL_DIR, ff)

    return 0, last_err


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
        return await loser.edit("✔ **لم يتم العثور على نتائج**")

    songname, url, duration, thumbnail = search
    await loser.edit("📥 **جاري تنزيل الفيديو... (قد يأخذ لحظات)**")

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
        return await m.reply_text("you're an __Anonymous__ user !\n\n» revert back to your real user account to use this bot.")

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

    loser = await c.send_message(chat_id, "🔄 **تتم المعالجة انتظر قليلآ...**")
    regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+"
    match = re.match(regex, link)
    if match:
        # لو YouTube — حمّل صوت مؤقت
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
            caption=f"💡 **تمت إضافة المسار إلى قائمة الانتظار »** `{pos}`\n\n💭 **المجموعه:** `{chat_id}`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})")
    else:
        try:
            await loser.edit("🔄 **جاري التشغيل انتظر قليلآ...**")
            await call_py.play(chat_id, MediaStream(livelink, AudioQuality.HIGH, vq))
            add_to_queue(chat_id, "Live Stream", livelink, link, "Video", Q)
            await loser.delete()
            buttons = stream_markup(user_id)
            await m.reply_photo(photo=f"{IMG_2}", reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"💡 **[فيديو مباشر]({link}) بدء التشغيل**\n\n💭 **المجموعه:** `{chat_id}`\n💡 **الحالة:** `شغال`\n🎧 **طلب بواسطة:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})")
        except Exception as ep:
            await loser.delete()
            await m.reply_text(f"🚫 خطأ: `{ep}`")
