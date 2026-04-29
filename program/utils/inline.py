""" inline section button """

from pyrogram.types import (
  CallbackQuery,
  InlineKeyboardButton,
  InlineKeyboardMarkup,
  Message,
)
from config import UPDATES_CHANNEL, BOT_USERNAME


def _btn(text, style=None, **kwargs):
  """ينشئ InlineKeyboardButton ويحاول تطبيق ميزة style (تلوين الأزرار - Bot API 9.4+).
  لو نسخة Pyrogram لا تدعم style بعد، يتم تجاهله تلقائياً بدون أن يكسر البوت."""
  btn = InlineKeyboardButton(text=text, **kwargs)
  if style:
    try:
      setattr(btn, "style", style)
    except Exception:
      pass
  return btn


def stream_markup(user_id):
  """أزرار التحكم تظهر مباشرة في رسالة التشغيل — بدون زر قائمة منفصل.
  زرّان فقط: كتم الصوت / إلغاء الكتم — مع تلوين كل زر بلونه المناسب
  وفق ميزة Telegram Bot API 9.4 (style).
  ملاحظة: شريط التقدم يُضاف تلقائياً فوق هذه الأزرار من progress_bar.py"""
  channel_url = f"https://t.me/{UPDATES_CHANNEL}" if UPDATES_CHANNEL else "https://t.me/"
  bot_username = BOT_USERNAME or "WorldMusicly_Bot"
  buttons = [
    [
      _btn("🔇", style="danger",  callback_data=f'cbmute | {user_id}'),
      _btn("🔊", style="success", callback_data=f'cbunmute | {user_id}'),
    ],
    [
      _btn("الـتـحـديـثـات", style="primary", url=channel_url),
    ],
    [
      _btn("اضـف الـبـوت لـمـجـمـوعـتـك", style="primary",
           url=f'https://t.me/{bot_username}?startgroup=true'),
    ],
  ]
  return buttons


def menu_markup(user_id):
  """قائمة /menu التفصيلية — تحتفظ بكل أزرار التحكم."""
  buttons = [
    [
      _btn("⏹", style="danger",  callback_data=f'cbstop | {user_id}'),
      _btn("⏸", style="primary", callback_data=f'cbpause | {user_id}'),
      _btn("▶️", style="success", callback_data=f'cbresume | {user_id}'),
    ],
    [
      _btn("🔇", style="danger",  callback_data=f'cbmute | {user_id}'),
      _btn("🔊", style="success", callback_data=f'cbunmute | {user_id}'),
    ],
    [
      _btn("اغلاق", style="danger", callback_data='cls'),
    ]
  ]
  return buttons


close_mark = InlineKeyboardMarkup(
  [
    [
      _btn("رجوع", style="primary", callback_data="cbmenu")
    ]
  ]
)


back_mark = InlineKeyboardMarkup(
  [
    [
      _btn("رجوع", style="primary", callback_data="cbmenu")
    ]
  ]
)
