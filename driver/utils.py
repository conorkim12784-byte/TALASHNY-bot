# utils.py — أدوات مساعدة (skip_current_song, skip_item, bash, keyboard)
#
# 🔧 إصلاح مهم: شيلنا الـ @call_py.on_update() اللي كان هنا لأنه كان بيتعارض
# مع نفس الـ handler الموجود في callsmusic/callsmusic.py
# (الاتنين كانوا بيمسكوا StreamEnded ويعملوا skip → بيحصل تشغيل مزدوج / مغادرة مرتين)
#
# الـ handler الوحيد دلوقتي موجود في callsmusic/callsmusic.py
# (مسجّل في main.py عبر register_stream_end_handler)

import asyncio

from driver.queues import QUEUE, clear_queue, get_queue, pop_an_item
from driver.veez import bot, call_py
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
from config import UPDATES_CHANNEL, BOT_USERNAME

_channel_url = f"https://t.me/{UPDATES_CHANNEL}" if UPDATES_CHANNEL else "https://t.me/"
_bot_username = BOT_USERNAME or "WorldMusicly_Bot"

keyboard = InlineKeyboardMarkup(
    [
            [
                InlineKeyboardButton(text="• الـقـائـمـه♪", callback_data="cbmenu"),
                InlineKeyboardButton("• الـتـحـديـثـات♪", url=_channel_url),
            ],
            [
                InlineKeyboardButton(
                        "♡اضـف الـبـوت لـمـجـمـوعـتـك♡",
                        url=f"https://t.me/{_bot_username}?startgroup=true"
                )
            ],
        ]
    )


async def skip_current_song(chat_id):
    """تستخدم في أمر /تخطي — تشغل المقطع التالي يدوياً.

    التعديل المهم:
    - لو القائمة مفيهاش غير الأغنية الحالية فقط (مفيش تالي) → نرجّع 0
      (= القائمة فارغة) من غير ما نغلق المكالمة. المستخدم اللي يقرر ينهي
      التشغيل بأمر "انهاء" بنفسه.
    - بنستبدل الستريم الحالي بستريم جديد بشكل واضح (نفس play لكن مضمون
      يقاطع الأغنية الحالية لأن pytgcalls.play() على نفس chat_id بيحل
      محل الستريم النشط).
    """
    if chat_id not in QUEUE:
        return 0

    chat_queue = get_queue(chat_id)

    # مفيش أغنية تالية — مانعملش leave، بس نبلّغ إن القائمة فارغة
    if len(chat_queue) <= 1:
        return 0

    try:
        songname = chat_queue[1][0]
        url      = chat_queue[1][1]
        link     = chat_queue[1][2]
        type_    = chat_queue[1][3]
        Q        = chat_queue[1][4]

        # شيل الأغنية الحالية من القائمة الأول عشان الـ stream-end handler
        # ميلخبطش الترتيب لو خلصت الأغنية الجديدة بعد كده.
        pop_an_item(chat_id)

        if type_ == "Audio":
            await call_py.play(
                chat_id,
                MediaStream(url, AudioQuality.HIGH),
            )
        elif type_ == "Video":
            if Q == 720:
                vq = VideoQuality.HD_720p
            elif Q == 480:
                vq = VideoQuality.SD_480p
            elif Q == 360:
                vq = VideoQuality.SD_360p
            else:
                vq = VideoQuality.HD_720p
            await call_py.play(
                chat_id,
                MediaStream(url, AudioQuality.HIGH, vq),
            )
        else:
            await call_py.play(
                chat_id,
                MediaStream(url, AudioQuality.HIGH),
            )

        return [songname, link, type_]
    except Exception as e:
        print(f"[skip_current_song error] {e}")
        try:
            await call_py.leave_call(chat_id)
        except Exception:
            pass
        clear_queue(chat_id)
        return 2


async def skip_item(chat_id, h):
    if chat_id in QUEUE:
        chat_queue = get_queue(chat_id)
        try:
            x = int(h)
            songname = chat_queue[x][0]
            chat_queue.pop(x)
            return songname
        except Exception as e:
            print(e)
            return 0
    else:
        return 0


# ❌ شيلنا هنا الـ @call_py.on_update() لأنه كان مكرر مع callsmusic/callsmusic.py


async def bash(cmd):
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    err = stderr.decode().strip()
    out = stdout.decode().strip()
    return out, err
