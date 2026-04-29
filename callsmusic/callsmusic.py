import os
import asyncio
from pyrogram.errors import FloodWait
from pytgcalls.types import Update, StreamEnded, MediaStream, AudioQuality, VideoQuality
from . import queues  # legacy — kept for backwards compatibility
from driver.queues import QUEUE, pop_an_item, clear_queue, get_queue
from driver.veez import bot
from driver.design.thumbnail import thumb
from driver.design.chatname import CHAT_TITLE
from program.utils.inline import stream_markup
from program.utils.progress_bar import stop_progress, hide_buttons, start_progress
from pyrogram.types import InlineKeyboardMarkup
from config import IMG_5
import re


def _yt_thumb_from_link(link: str) -> str:
    if not link or not isinstance(link, str):
        return IMG_5
    m = re.search(r"(?:v=|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})", link)
    if m:
        return f"https://i.ytimg.com/vi/{m.group(1)}/hqdefault.jpg"
    return IMG_5


async def register_stream_end_handler(call_py):

    @call_py.on_update()
    async def on_stream_end(client, update: Update) -> None:
        if not isinstance(update, StreamEnded):
            return

        chat_id = update.chat_id

        # امسح ملف الأغنية اللي خلصت لو كانت ملف محلي في /tmp
        try:
            chat_queue = get_queue(chat_id)
            if chat_queue and len(chat_queue) > 0:
                finished = chat_queue[0]
                fp = finished[1] if len(finished) > 1 else ""
                if isinstance(fp, str) and fp.startswith("/tmp") and os.path.exists(fp):
                    try:
                        os.remove(fp)
                    except Exception:
                        pass
        except Exception:
            pass

        # شيل الأغنية المنتهية من القائمة
        pop_an_item(chat_id)

        # وقف شريط التقدم وأخفي أزرار الرسالة الخاصة بالأغنية المنتهية
        await hide_buttons(chat_id)

        chat_queue = get_queue(chat_id)
        if not chat_queue or len(chat_queue) == 0:
            # القائمة فاضية — اخرج من الكول ونظّف بالكامل عشان التشغيل اللي جاي
            # يعمل join + ensure_group_call_started من جديد بنجاح
            try:
                await call_py.leave_call(chat_id)
            except Exception as e:
                print(f"[leave_call error] {e}")
            clear_queue(chat_id)
            stop_progress(chat_id)
            return

        # شغّل الأغنية التالية
        try:
            nxt = chat_queue[0]
            songname = nxt[0]
            stream_source = nxt[1]
            ref_url = nxt[2]
            type_ = nxt[3] if len(nxt) > 3 else "Audio"
            quality = nxt[4] if len(nxt) > 4 else 0
            duration = nxt[5] if len(nxt) > 5 else 0

            if type_ == "Video":
                if quality == 720:
                    vq = VideoQuality.HD_720p
                elif quality == 480:
                    vq = VideoQuality.SD_480p
                elif quality == 360:
                    vq = VideoQuality.SD_360p
                else:
                    vq = VideoQuality.HD_720p
                ms = MediaStream(stream_source, AudioQuality.HIGH, vq)
            else:
                ms = MediaStream(
                    stream_source,
                    audio_parameters=AudioQuality.HIGH,
                    audio_flags=MediaStream.Flags.AUTO_DETECT,
                    video_flags=MediaStream.Flags.IGNORE,
                )

            await call_py.play(chat_id, ms)

            # ابعت رسالة الأغنية الجديدة بنفس شكل التشغيل العادي
            try:
                gcname = ""
                try:
                    chat = await bot.get_chat(chat_id)
                    gcname = chat.title or ""
                except Exception:
                    pass
                ctitle = await CHAT_TITLE(gcname)
                song_thumb_url = _yt_thumb_from_link(ref_url)
                image = await thumb(
                    song_thumb_url, songname, 0, ctitle,
                    requester="", duration=duration if isinstance(duration, int) else 0,
                )
                buttons = stream_markup(0)
                sent = await bot.send_photo(
                    chat_id,
                    photo=image,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    caption=(
                        f"**تم تشغيل الموسيقى.**\n\n"
                        f"**الاسم:** [{songname}]({ref_url})\n"
                        f"**المدة:** `{duration if duration else 'غير معروف'}`"
                    ),
                )
                try:
                    dur_secs = duration if isinstance(duration, int) else 0
                    await start_progress(bot, chat_id, sent, dur_secs, 0)
                except Exception as e:
                    print(f"[auto-next start_progress] {e}")
            except Exception as e:
                print(f"[auto-next send message] {e}")

        except Exception as e:
            print(f"[play next track error] {e}")
