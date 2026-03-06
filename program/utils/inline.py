""" inline section button """

from pyrogram.types import (
  CallbackQuery,
  InlineKeyboardButton,
  InlineKeyboardMarkup,
  Message,
)


def stream_markup(user_id):
  buttons = [
    [
      InlineKeyboardButton(text="• الـقـائـمـه♪", callback_data=f'cbmenu | {user_id}'),
      InlineKeyboardButton(text="• الـتـحـديـثـات♪", url=f'https://t.me/FW_TF'),
    ],
    [
    InlineKeyboardButton(
                        "♡اضـف الـبـوت لـمـجـمـوعـتـك♡",
                        url=f'https://t.me/WorldMusicly_Bot?startgroup=true'),
    ],
  ]
  return buttons


def menu_markup(user_id):
  buttons = [
    [
      InlineKeyboardButton(text="⏹", callback_data=f'cbstop | {user_id}'),
      InlineKeyboardButton(text="⏸", callback_data=f'cbpause | {user_id}'),
      InlineKeyboardButton(text="▶️", callback_data=f'cbresume | {user_id}'),
    ],
    [
      InlineKeyboardButton(text="🔇", callback_data=f'cbmute | {user_id}'),
      InlineKeyboardButton(text="🔊", callback_data=f'cbunmute | {user_id}'),
    ],
    [
      InlineKeyboardButton(text="🗑 اغلاق", callback_data='cls'),
    ]
  ]
  return buttons


close_mark = InlineKeyboardMarkup(
  [
    [
      InlineKeyboardButton(
        "🔙 رجوع", callback_data="cbmenu"
      )
    ]
  ]
)


back_mark = InlineKeyboardMarkup(
  [
    [
      InlineKeyboardButton(
        "🔙 رجوع", callback_data="cbmenu"
      )
    ]
  ]
)
