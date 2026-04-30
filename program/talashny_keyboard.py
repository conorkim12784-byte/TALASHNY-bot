# talashny_keyboard.py — أمر "كيبورد تلاشاني"
#
# كيف يعمل؟
# 1) يكتب أي مشرف/صاحب بوت: "كيبورد تلاشاني"
#    -> البوت يرد: "اكتب اسم الكيبورد"
# 2) المستخدم يكتب الاسم
#    -> البوت يرسل ReplyKeyboard فيه زرّان:
#         [اسم اللي كتبه]   و   [حذف الكيبورد]
# 3) لما يضغط "حذف الكيبورد" -> يختفي الـ ReplyKeyboard.
#
# مسموح: SUDO_USERS + creator + administrators (مش الأعضاء العاديين).

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

from driver.filters import command, command2, other_filters
from config import SUDO_USERS

# user_id -> True (في انتظار اسم الكيبورد)
_pending_kb: dict = {}


def _status_str(status) -> str:
    if status is None:
        return ""
    return getattr(status, "value", str(status)).lower()


async def _is_admin_or_sudo(c: Client, chat_id: int, user_id: int) -> bool:
    if user_id is None:
        return False
    if user_id in SUDO_USERS:
        return True
    try:
        member = await c.get_chat_member(chat_id, user_id)
        return _status_str(member.status) in ("administrator", "creator", "owner")
    except Exception:
        return False


# ─────────────────────────────────────────────
# 1) الأمر "كيبورد تلاشاني"
# ─────────────────────────────────────────────
@Client.on_message(
    (command(["talashny_kb", "tkb"])
     | command2(["كيبورد تلاشاني", "كيبورد_تلاشاني", "كيبورد"]))
    & filters.group
)
async def talashny_keyboard_start(c: Client, m: Message):
    if not m.from_user:
        return
    if not await _is_admin_or_sudo(c, m.chat.id, m.from_user.id):
        return await m.reply("❌ هذا الأمر للمشرفين وأصحاب البوت فقط")

    _pending_kb[m.from_user.id] = m.chat.id
    await m.reply(
        "⌨️ **اكتب اسم الكيبورد**\n\n"
        "_(للإلغاء اكتب: `الغاء`)_"
    )


# ─────────────────────────────────────────────
# 2) التقاط الاسم اللي بعتُه المستخدم بعد الأمر
# ─────────────────────────────────────────────
@Client.on_message(filters.text & filters.group & ~filters.via_bot, group=9)
async def _capture_kb_name(c: Client, m: Message):
    if not m.from_user:
        return
    uid = m.from_user.id
    if _pending_kb.get(uid) != m.chat.id:
        return

    txt = (m.text or "").strip()
    if not txt:
        return

    # تجاهل أوامر تانية
    if txt.startswith(("/", "!", ".")):
        return
    if txt in ("حذف الكيبورد", "إخفاء الكيبورد"):
        return  # هندلر تاني هيتعامل معاها

    if txt.lower() in ("الغاء", "إلغاء", "cancel"):
        _pending_kb.pop(uid, None)
        return await m.reply("✘ تم الإلغاء", reply_markup=ReplyKeyboardRemove())

    # خلاص — هنبني الكيبورد
    name = txt[:40]  # حد أقصى للاسم
    _pending_kb.pop(uid, None)

    kb = ReplyKeyboardMarkup(
        [
            [KeyboardButton(name)],
            [KeyboardButton("حذف الكيبورد")],
        ],
        resize_keyboard=True,
        selective=True,  # يظهر فقط للشخص اللي كتب الأمر
    )
    await m.reply(
        f"✔ **تم إنشاء الكيبورد**: `{name}`",
        reply_markup=kb,
    )


# ─────────────────────────────────────────────
# 3) زر "حذف الكيبورد" -> يشيل الـ ReplyKeyboard
# ─────────────────────────────────────────────
@Client.on_message(filters.regex(r"^حذف الكيبورد$") & filters.group)
async def remove_talashny_kb(c: Client, m: Message):
    await m.reply(
        "✔ تم إخفاء الكيبورد",
        reply_markup=ReplyKeyboardRemove(selective=True),
    )
