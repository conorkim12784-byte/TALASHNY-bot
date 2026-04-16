import re
import asyncio
import os

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
from program.ytsearch_core import ytsearch, ytsearch_yt

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


def _dm_search(query: str):
    ydl_opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}
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
    ydl_opts = {"quiet": True, "no_warnings": True, "format": "bestaudio/best", "outtmpl": out_tpl}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        return None
    except Exception as e:
        print(f"[sc_download error] {e}")
        return str(e)


def _start_bgutil_server():
    """تشغيل bgutil PO token server في الخلفية لو مش شغال"""
    import subprocess, time
    try:
        import urllib.request as _ur
        _ur.urlopen("http://localhost:4416/get_visitor_data", timeout=2)
        return  # شغال بالفعل
    except Exception:
        pass
    try:
        bgutil_path = "/bgutil/server/build/main.js"
        if os.path.isfile(bgutil_path):
            subprocess.Popen(
                ["node", bgutil_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(3)
            print("[bgutil] server started")
    except Exception as e:
        print(f"[bgutil] failed to start: {e}")


def _build_ydl_opts(fmt: str, use_pot: bool = False) -> dict:
    """بناء ydl_opts الأساسية مع دعم PO Token و cookies"""
    base = {
        "format": fmt,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "skip_download": True,
    }

    # cookies.txt لو موجود
    cookies_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cookies.txt")
    if os.path.isfile(cookies_file):
        base["cookiefile"] = cookies_file

    # bgutil PO Token provider
    if use_pot:
        try:
            base["extractor_args"] = {
                "youtube": {
                    "player_client": ["web"],
                    "po_token": ["web+https://bgutil-ytdlp-pot-provider.korkmazgokhan.workers.dev/get_po_token"],
                }
            }
        except Exception:
            pass

    return base


def _extract_url_from_info(info: dict) -> str | None:
    url = info.get("url")
    if not url and info.get("requested_formats"):
        url = info["requested_formats"][0].get("url")
    if not url and info.get("formats"):
        for f in reversed(info["formats"]):
            if f.get("url") and not f["url"].startswith("manifest"):
                url = f["url"]
                break
    return url


def _ydl_get_url(link: str, fmt: str) -> tuple:
    # تشغيل bgutil server تلقائياً
    _start_bgutil_server()

    # قائمة الاستراتيجيات بالترتيب
    strategies = [
        # الأولوية: web مع bgutil PO token (الأقوى ضد الحجب)
        {
            "use_pot": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["web"],
                }
            },
            "label": "web+bgutil_pot",
        },
        # ios مع User-Agent الحقيقي
        {
            "use_pot": False,
            "extractor_args": {
                "youtube": {"player_client": ["ios"]}
            },
            "http_headers": {
                "User-Agent": "com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)"
            },
            "label": "ios",
        },
        # android مع User-Agent الحقيقي
        {
            "use_pot": False,
            "extractor_args": {
                "youtube": {"player_client": ["android"]}
            },
            "http_headers": {
                "User-Agent": "com.google.android.youtube/19.29.37 (Linux; U; Android 14; en_US; Pixel 8; Build/UQ1A.240605.004;) gzip"
            },
            "label": "android",
        },
        # tv_embedded
        {
            "use_pot": False,
            "extractor_args": {
                "youtube": {"player_client": ["tv_embedded"], "skip": ["webpage"]}
            },
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (SMART-TV; Linux; Tizen 6.0) AppleWebKit/538.1 (KHTML, like Gecko) Version/6.0 TV Safari/538.1"
            },
            "label": "tv_embedded",
        },
        # web_creator
        {
            "use_pot": False,
            "extractor_args": {
                "youtube": {"player_client": ["web_creator"]}
            },
            "label": "web_creator",
        },
    ]

    for strategy in strategies:
        label = strategy.pop("label")
        use_pot = strategy.pop("use_pot")
        ydl_opts = _build_ydl_opts(fmt, use_pot=use_pot)
        ydl_opts.update(strategy)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                url = _extract_url_from_info(info)
                if url:
                    print(f"[ydl_get_url] ✓ OK via {label}")
                    return 1, url
        except Exception as e:
            print(f"[ydl_get_url] ✗ {label} failed: {str(e)[:120]}")

    return 0, "فشل تحميل الأغنية — الـ IP محجوب من YouTube، جرب تضيف cookies.txt"


async def ytdl_audio(link):
    return await asyncio.to_thread(_ydl_get_url, link, "bestaudio/best")

ytdl = ytdl_audio

async def ytdl_video(link, quality=720):
    return await asyncio.to_thread(_ydl_get_url, link, f"best[height<=?{quality}][width<=?1280]/best")

async def _auto_delete(filepath: str, delay: int = 600):
    await asyncio.sleep(delay)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass

def multisearch_video(query: str):
    result = ytsearch_yt(query)
    if result and isinstance(result, list) and len(result) == 4:
        return result
    return None

def get_video_quality(Q):
    if Q == 480: return VideoQuality.SD_480p
    elif Q == 360: return VideoQuality.SD_360p
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
        return await m.reply_text("you're an __Anonymous__ user !")
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
    if not search:
        return await loser.edit("✘ **لم يتم العثور على نتائج**")
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
                try: os.remove(filepath)
                except: pass
            asyncio.create_task(cleanup())
        except Exception as ep:
            try: os.remove(filepath)
            except: pass
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
        link = m.text.split(None, 1)[1]; Q = 720
    elif len(m.command) == 3:
        op = m.text.split(None, 1)[1]
        link = op.split(None, 1)[0]
        quality = op.split(None, 1)[1]
        Q = int(quality) if quality in ("720", "480", "360") else 720
    else:
        return await m.reply("**/vstream {link} {720/480/360}**")
    loser = await c.send_message(chat_id, "🔄 **تتم المعالجة...**")
    regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+"
    if re.match(regex, link):
        veez, livelink = await ytdl_audio(link)
    else:
        livelink = link; veez = 1
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
