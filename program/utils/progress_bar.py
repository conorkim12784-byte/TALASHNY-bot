"""
شريط تقدم تلقائي يظهر فوق أزرار التحكم في رسالة التشغيل.
زر واحد على شكل:   1:23 ▰▰▰▰▱▱▱▱▱▱ 3:45
يتحدّث تلقائياً كل 5 ثوانٍ بدون التأثير على حدود تيليجرام
(edit_message_reply_markup فقط — أخف بكثير من تعديل النص/الصورة).

الاستخدام:
    from program.utils.progress_bar import start_progress, stop_progress
    await start_progress(client, chat_id, message, duration_secs, user_id)
    # عند الإيقاف/التخطي/نهاية الأغنية:
    stop_progress(chat_id)
"""

import asyncio
import time
from typing import Dict, Optional

from pyrogram import Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from .inline import stream_markup

# مهام شغّالة لكل دردشة (chat_id -> asyncio.Task)
_TASKS: Dict[int, asyncio.Task] = {}
# وقت بداية الأغنية (chat_id -> epoch seconds)
_STARTED_AT: Dict[int, float] = {}


BAR_LEN = 12  # عدد الخانات في الشريط


def _fmt_time(secs: int) -> str:
    if secs < 0:
        secs = 0
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _build_bar(elapsed: int, total: int) -> str:
    if total <= 0:
        # مفيش مدة معروفة — نعرض شريط متحرك بسيط
        idx = (elapsed // 2) % BAR_LEN
        cells = ["▱"] * BAR_LEN
        cells[idx] = "▰"
        return f"{_fmt_time(elapsed)} {''.join(cells)} LIVE"
    filled = int(BAR_LEN * min(elapsed, total) / total)
    bar = "▰" * filled + "▱" * (BAR_LEN - filled)
    return f"{_fmt_time(elapsed)} {bar} {_fmt_time(total)}"


def _build_markup(user_id: int, elapsed: int, total: int) -> InlineKeyboardMarkup:
    """يجمع صف شريط التقدم فوق أزرار التحكم العادية."""
    progress_btn = InlineKeyboardButton(
        text=_build_bar(elapsed, total),
        callback_data="progress_noop",
    )
    rows = [[progress_btn]] + stream_markup(user_id)
    return InlineKeyboardMarkup(rows)


async def _runner(client: Client, chat_id: int, message: Message,
                  duration: int, user_id: int):
    """يحدّث الأزرار كل 3 ثوانٍ حتى تنتهي الأغنية أو يتم الإيقاف."""
    interval = 3
    last_text = None
    fail_count = 0
    try:
        while True:
            elapsed = int(time.time() - _STARTED_AT.get(chat_id, time.time()))
            if duration > 0 and elapsed >= duration:
                try:
                    await client.edit_message_reply_markup(
                        chat_id=message.chat.id,
                        message_id=message.id,
                        reply_markup=_build_markup(user_id, duration, duration),
                    )
                except Exception:
                    pass
                break

            new_markup = _build_markup(user_id, elapsed, duration)
            # تحقق إن الشريط فعلاً اتغيّر قبل الإرسال (تيليجرام يرفض نفس المحتوى)
            current_text = new_markup.inline_keyboard[0][0].text
            if current_text != last_text:
                try:
                    await client.edit_message_reply_markup(
                        chat_id=message.chat.id,
                        message_id=message.id,
                        reply_markup=new_markup,
                    )
                    last_text = current_text
                    fail_count = 0
                except Exception as e:
                    fail_count += 1
                    print(f"[progress_bar] edit failed ({fail_count}): {e}")
                    if fail_count >= 5:
                        break

            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        pass
    finally:
        _TASKS.pop(chat_id, None)
        _STARTED_AT.pop(chat_id, None)


async def start_progress(client: Client, chat_id: int, message: Message,
                         duration: int, user_id: int):
    """يبدأ شريط التقدم لأغنية جديدة. يلغي أي شريط سابق على نفس الدردشة."""
    stop_progress(chat_id)
    _STARTED_AT[chat_id] = time.time()
    # عرض فوري بالقيم الابتدائية
    try:
        await client.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.id,
            reply_markup=_build_markup(user_id, 0, duration),
        )
    except Exception:
        pass
    task = asyncio.create_task(
        _runner(client, chat_id, message, duration, user_id)
    )
    _TASKS[chat_id] = task


def stop_progress(chat_id: int):
    """يوقف شريط التقدم لدردشة محددة."""
    task = _TASKS.pop(chat_id, None)
    _STARTED_AT.pop(chat_id, None)
    if task and not task.done():
        task.cancel()
