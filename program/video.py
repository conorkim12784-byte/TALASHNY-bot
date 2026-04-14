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
from driver.utils import bash
from pyrogram import Client
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant, PeerIdInvalid
from pyrogram.types import InlineKeyboardMarkup, Message
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
import yt_dlp
import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from ytdl_utils import COOKIES_FILE

DL_DIR = "/tmp/tgbot_vids"
AUDIO_DIR = "/tmp/tgbot_audio"
os.makedirs(DL_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# Piped API fallback proxies (disabled by default — set to {} if no proxy needed)
TOR_PROXIES = {}


def _parse_duration(seconds) -> str:
    if not seconds:
        return "0:00"
    seconds = int(seconds)
    mins, secs = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"


def ytsearch(query: str):
    """بحث الصوت — YouTube Data API v3"""
    import re as _re2
    import requests as _req
    try:
        from config import YOUTUBE_API_KEY
        r = _req.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={"part": "snippet", "q": query, "type": "video",
                    "maxResults": 1, "key": YOUTUBE_API_KEY},
            timeout=10,
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        if not items:
            print("[ytsearch] no results")
            return None
        item = items[0]
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"][:70]
        thumbnail = item["snippet"]["thumbnails"].get("high", {}).get("url", "")
        r2 = _req.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"part": "contentDetails", "id": video_id, "key": YOUTUBE_API_KEY},
            timeout=10,
        )
        r2.raise_for_status()
        detail = r2.json().get("items", [])
        iso = detail[0]["contentDetails"]["duration"] if detail else "PT0S"
        mt = _re2.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
        h, m, s = (int(mt.group(i) or 0) for i in (1, 2, 3)) if mt else (0, 0, 0)
        total = h * 3600 + m * 60 + s
        mins, secs = divmod(total, 60)
        hrs, mins = divmod(mins, 60)
        duration = f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"
        url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"[ytsearch] YouTube API: {title}")
        return [title, url, duration, thumbnail]
    except Exception as e:
        print(f"[ytsearch error] {e}")
        return None


def ytsearch_yt(query: str):
    """بحث فيديو — YouTube Data API v3"""
    import re as _re2
    import requests as _req
    try:
        from config import YOUTUBE_API_KEY
        r = _req.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={"part": "snippet", "q": query, "type": "video",
                    "maxResults": 1, "key": YOUTUBE_API_KEY},
            timeout=10,
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        if not items:
            print("[ytsearch_yt] no results")
            return None
        item = items[0]
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"][:70]
        thumbnail = item["snippet"]["thumbnails"].get("high", {}).get("url", "")
        r2 = _req.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"part": "contentDetails", "id": video_id, "key": YOUTUBE_API_KEY},
            timeout=10,
        )
        r2.raise_for_status()
        detail = r2.json().get("items", [])
        iso = detail[0]["contentDetails"]["duration"] if detail else "PT0S"
        mt = _re2.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
        h, m, s = (int(mt.group(i) or 0) for i in (1, 2, 3)) if mt else (0, 0, 0)
        total = h * 3600 + m * 60 + s
        mins, secs = divmod(total, 60)
        hrs, mins = divmod(mins, 60)
        duration = f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"
        url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"[ytsearch_yt] YouTube API: {title}")
        return [title, url, duration, thumbnail]
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


def _get_piped_streams(video_id: str):
    """جيب streams الفيديو والصوت من Piped API بدون cookies"""
    import requests
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.tokhmi.xyz",
        "https://pipedapi.moomoo.me",
        "https://api.piped.projectsegfau.lt",
        "https://pipedapi.in.projectsegfau.lt",
    ]
    for base in instances:
        try:
            r = requests.get(f"{base}/streams/{video_id}", proxies=TOR_PROXIES, timeout=10)
            if r.status_code != 200:
                continue
            data = r.json()
            video_streams = data.get("videoStreams", [])
            audio_streams = data.get("audioStreams", [])

            # فيديو مدمج (بيكون أسهل)
            combined = [s for s in video_streams if s.get("videoOnly") == False and s.get("url")]
            if combined:
                best = sorted(combined, key=lambda x: x.get("quality", ""), reverse=True)
                return {"type": "combined", "url": best[0]["url"]}

            # فيديو + صوت منفصلين
            video_only = [s for s in video_streams if s.get("url")]
            audio_only = [s for s in audio_streams if s.get("url")]
            if video_only and audio_only:
                best_v = sorted(video_only, key=lambda x: x.get("quality", ""), reverse=True)[0]["url"]
                best_a = sorted(audio_only, key=lambda x: x.get("quality", ""), reverse=True)[0]["url"]
                return {"type": "separate", "video": best_v, "audio": best_a}

        except Exception as e:
            print(f"[piped {base}] {e}")
    return None


def _download_piped(streams: dict, out_tpl: str) -> bool:
    """حمّل من Piped streams مباشرة"""
    import requests, uuid as _uuid, subprocess
    uid = _uuid.uuid4().hex[:8]

    if streams["type"] == "combined":
        try:
            r = requests.get(streams["url"], stream=True, proxies=TOR_PROXIES, timeout=60)
            ext = "mp4"
            fname = out_tpl.replace("%(ext)s", ext)
            with open(fname, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"[piped combined dl] {e}")
            return False

    elif streams["type"] == "separate":
        try:
            v_file = f"/tmp/{uid}_v.mp4"
            a_file = f"/tmp/{uid}_a.m4a"
            out_file = out_tpl.replace("%(ext)s", "mp4")

            for url, path in [(streams["video"], v_file), (streams["audio"], a_file)]:
                r = requests.get(url, stream=True, proxies=TOR_PROXIES, timeout=60)
                with open(path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            # دمج بـ ffmpeg
            subprocess.run([
                "ffmpeg", "-y",
                "-i", v_file, "-i", a_file,
                "-c:v", "copy", "-c:a", "aac",
                out_file
            ], capture_output=True)

            import os
            for f in [v_file, a_file]:
                try: os.remove(f)
                except: pass
            return True
        except Exception as e:
            print(f"[piped separate dl] {e}")
            return False
    return False


def _yt_download_video(link: str, out_tpl: str, fmt: str) -> str | None:
    """تحميل فيديو — عبر Piped API بدون cookies"""
    import re as _re

    # استخرج video ID
    match = _re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", link)
    if not match:
        return "invalid youtube link"

    video_id = match.group(1)

    # جرب Piped
    streams = _get_piped_streams(video_id)
    if streams:
        success = _download_piped(streams, out_tpl)
        if success:
            return None

    return "piped failed"


def _dm_download_video(link: str, out_tpl: str, fmt: str) -> str | None:
    """تحميل فيديو من Dailymotion"""
    ydl_opts = {
        "quiet": True, "no_warnings": True,
        "format": fmt, "outtmpl": out_tpl,
        "merge_output_format": "mp4", "prefer_free_formats": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        return None
    except Exception as e:
        print(f"[dm_dl_video error] {e}")
        return str(e)


async def ytdl_direct(link: str):
    """جيب رابط مباشر من يوتيوب بدون تحميل — yt-dlp -g"""
    import asyncio
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "-g",
        "--cookies", COOKIES_FILE,
        "-f", "best[height<=?720][width<=?1280]/best",
        link,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        url = stdout.decode().strip().split(chr(10))[0]
        return 1, url
    return 0, stderr.decode().strip()


def _ydl_get_url(link: str, fmt: str) -> tuple:
    """
    استخرج رابط مباشر عبر yt-dlp Python API.
    بيجرب: ios -> tv_embedded -> android -> web_creator
    proxy="" بيتجاوز أي system proxy بيبلوك YouTube.
    """
    clients = ["ios", "tv_embedded", "android", "web_creator"]

    # لو الـ fmt بيحتوي على height selector، نضيف fallback أشمل
    fallback_fmt = fmt
    if "height<=" in fmt:
        # مثلاً: best[height<=720] -> best[height<=720]/best
        if "/best" not in fmt:
            fallback_fmt = fmt + "/best"

    for client in clients:
        ydl_opts = {
            "format": fallback_fmt,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "proxy": "",
            "cookiefile": COOKIES_FILE,
            "extractor_args": {"youtube": {"player_client": [client]}},
            "skip_download": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                url = info.get("url") or (
                    info.get("requested_formats", [{}])[0].get("url")
                    if info.get("requested_formats") else None
                )
                if url:
                    print(f"[ydl_get_url] OK via client={client}")
                    return 1, url
        except Exception as e:
            print(f"[ydl_get_url] client={client} failed: {str(e)[:120]}")

    # آخر محاولة: نجرب "best" بدون أي قيود
    ydl_opts_fallback = {
        "format": "best",
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "proxy": "",
        "cookiefile": COOKIES_FILE,
        "extractor_args": {"youtube": {"player_client": ["ios"]}},
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts_fallback) as ydl:
            info = ydl.extract_info(link, download=False)
            url = info.get("url") or (
                info.get("requested_formats", [{}])[0].get("url")
                if info.get("requested_formats") else None
            )
            if url:
                print("[ydl_get_url] OK via fallback 'best'")
                return 1, url
    except Exception as e:
        print(f"[ydl_get_url] fallback failed: {str(e)[:120]}")

    return 0, "all extraction methods failed"


async def ytdl_audio(link):
    """جيب رابط مباشر للصوت — Python API بدون proxy"""
    return await asyncio.to_thread(_ydl_get_url, link, "bestaudio/best")


ytdl = ytdl_audio


async def ytdl_video(link, quality=720):
    """جيب رابط مباشر للفيديو — Python API بدون proxy"""
    return await asyncio.to_thread(
        _ydl_get_url, link, f"best[height<=?{quality}][width<=?1280]/best"
    )


async def _auto_delete(filepath: str, delay: int = 600):
    """حذف الملف تلقائياً بعد 10 دقائق"""
    await asyncio.sleep(delay)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass

def multisearch_video(query: str):
    """بحث الفيديو — YouTube عبر yt-dlp"""
    result = ytsearch_yt(query)
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
    except (UserNotParticipant, PeerIdInvalid):
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
