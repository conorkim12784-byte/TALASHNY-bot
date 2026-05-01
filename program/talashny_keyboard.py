"""
أمر «كيبورد تلاشاني»
- أي مشرف أو سودو/مالك يقدر يستخدمه (الأعضاء العاديين لأ)
- البوت يطلب اسم الكيبورد
- يستنى رسالة جديدة من نفس المستخدم (مش رسالة الأمر نفسها)
- يرد بـ ReplyKeyboardMarkup فيه الاسم + زر "حذف الكيبورد"
- الكيبورد selective=True عشان يظهر للطالب فقط
- زر "حذف الكيبورد" يشيل الـ ReplyKeyboard فقط
"""

import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

from driver.filters import command2
from driver.permissions import get_rank

# ذاكرة مؤقتة: { (chat_id, user_id): asyncio.Event/placeholder }
# بنخزن "بانتظار اسم" + الرسالة الأصلية
_pending: dict[tuple[int, int], dict] = {}

# بريفكسات الأوامر اللي لازم نتجاهلها لو المستخدم بعت أمر تاني بدل الاسم
_PREFIXES = ("/", "!", ".", "؟", "?", "#")
# كلمات لو الرسالة بدأت بيها يبقى دي أمر ثاني، نلغي الجلسة
_CANCEL_WORDS = {"الغاء", "إلغاء", "كنسل", "cancel", "خلاص"}


def _is_command_like(text: str) -> bool:
    if not text:
        return True
    t = text.strip()
    if not t:
        return True
    if t.startswith(_PREFIXES):
        return True
    # لو فيها كلمة "كيبورد" في الأول يبقى ده استدعاء جديد للأمر
    first = t.split()[0].lower()
    if first in {"كيبورد", "keyboard"}:
        return True
    return False


@Client.on_message(command2(["كيبورد", "كيبورد تلاشاني", "keyboard"]) & ~filters.private)
async def talashny_keyboard_cmd(client: Client, message: Message):
    if not message.from_user:
        return

    # تحقق صلاحية: مشرف أو سودو/مالك
    try:
        rank = await get_rank(client, message.chat.id, message.from_user.id)
    except Exception:
        rank = "member"

    if rank == "member":
        return await message.reply_text("• الأمر ده للمشرفين فقط.")

    key = (message.chat.id, message.from_user.id)
    _pending[key] = {"await_name": True, "request_msg_id": message.id}

    await message.reply_text(
        "✏️ ابعت دلوقتي اسم الكيبورد اللي عايزه.\n"
        "اكتب «الغاء» للإلغاء.",
        reply_to_message_id=message.id,
    )


@Client.on_message(filters.group & filters.text & ~filters.via_bot, group=50)
async def _capture_keyboard_name(client: Client, message: Message):
    if not message.from_user:
        return
    key = (message.chat.id, message.from_user.id)
    state = _pending.get(key)
    if not state or not state.get("await_name"):
        return

    # تجاهل لو الرسالة دي هي نفس رسالة الأمر
    if message.id == state.get("request_msg_id"):
        return

    text = (message.text or "").strip()

    # لو المستخدم بعت أمر تاني، نلغي الجلسة بدون رد
    if _is_command_like(text):
        _pending.pop(key, None)
        return

    if text.lower() in _CANCEL_WORDS:
        _pending.pop(key, None)
        return await message.reply_text("• تم الإلغاء.")

    # حد أقصى للاسم
    name = text[:40]

    _pending.pop(key, None)

    kb = ReplyKeyboardMarkup(
        [
            [KeyboardButton(name)],
            [KeyboardButton("حذف الكيبورد")],
        ],
        resize_keyboard=True,
        selective=True,  # يظهر للطالب فقط
    )

    await message.reply_text(
        f"✅ اتفضل كيبوردك: {name}",
        reply_markup=kb,
        reply_to_message_id=message.id,
    )


@Client.on_message(filters.group & filters.regex(r"^حذف الكيبورد$"))
async def _remove_keyboard(client: Client, message: Message):
    if not message.from_user:
        return
    await message.reply_text(
        "• تم حذف الكيبورد.",
        reply_markup=ReplyKeyboardRemove(selective=True),
        reply_to_message_id=message.id,
    )
