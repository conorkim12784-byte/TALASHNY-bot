"""
أوامر المالك:
- «المالك» → يعرض بيانات المالك الظاهر للبوت (اسم/يوزر/آيدي + زرار محادثة).
- «تغيير يوزر المالك» / «تغيير المالك» / «change_owner»
    → يغيّر المالك الظاهر للبوت (للمالك الرسمي/أصحاب البوت فقط).
- «تحديث المالك» / «ارجاع المالك» / «reset_owner»
    → يرجّع المالك الظاهر للمالك الرسمي.

ملاحظات:
- صلاحية تغيير/إرجاع المالك محصورة على OWNER_ID + SUDO_USERS، حتى
  لو حد تاني اتعمله "مالك ظاهر" قبل كده.
- يحفظ الحالة في owner_state.json
"""

import os
import json
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from driver.filters import command2

# استيراد آمن
try:
    from config import SUDO_USERS  # type: ignore
except Exception:
    SUDO_USERS = []

try:
    from config import OWNER_ID  # type: ignore
except Exception:
    # fallback: أول واحد في SUDO_USERS هو المالك الرسمي
    try:
        OWNER_ID = int(SUDO_USERS[0]) if SUDO_USERS else 0
    except Exception:
        OWNER_ID = 0

try:
    from config import OWNER_NAME  # type: ignore
except Exception:
    OWNER_NAME = "المالك"

STATE_FILE = "owner_state.json"

_pending: dict = {}

_PREFIXES = ("/", "!", ".", "؟", "?", "#")
_CANCEL_WORDS = {"الغاء", "إلغاء", "كنسل", "cancel", "خلاص"}


def _load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(data: dict) -> None:
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _sudo_list() -> list:
    try:
        return [int(x) for x in (SUDO_USERS or [])]
    except Exception:
        try:
            return list(SUDO_USERS or [])
        except Exception:
            return []


def _is_real_owner(user_id: int) -> bool:
    if not user_id:
        return False
    try:
        if OWNER_ID and int(user_id) == int(OWNER_ID):
            return True
    except Exception:
        pass
    if int(user_id) in _sudo_list():
        return True
    return False


def _is_command_like(text: str) -> bool:
    if not text:
        return True
    t = text.strip()
    if not t:
        return True
    if t.startswith(_PREFIXES):
        return True
    first = t.split()[0]
    if first in {"تغيير", "المالك", "تحديث", "ارجاع", "إرجاع"}:
        return True
    return False


def get_display_owner_id() -> int:
    data = _load_state()
    try:
        return int(data.get("display_owner_id") or OWNER_ID or 0)
    except Exception:
        return 0


def get_display_owner_username() -> str:
    data = _load_state()
    return str(data.get("display_owner_username") or "") or ""


def get_display_owner_name() -> str:
    data = _load_state()
    return str(data.get("display_owner_name") or OWNER_NAME or "المالك")


# ═══════════════════════════════════════
# أمر: عرض المالك (لكل الأعضاء)
# ═══════════════════════════════════════
@Client.on_message(command2(["المالك", "مالك", "owner"]))
async def show_owner_cmd(client: Client, message: Message):
    oid = get_display_owner_id()
    oname = get_display_owner_name()
    ouser = get_display_owner_username()

    # نحاول نجيب أحدث بيانات من تليجرام
    if oid:
        try:
            u = await client.get_users(oid)
            oname = (u.first_name or "") + ((" " + u.last_name) if u.last_name else "")
            oname = oname.strip() or oname or "المالك"
            ouser = u.username or ouser
            # نحدّث الحالة بالاسم الجديد لو اتغير
            data = _load_state()
            if oname:
                data["display_owner_name"] = oname
            if ouser:
                data["display_owner_username"] = ouser
            _save_state(data)
        except Exception:
            pass

    user_link = f"tg://user?id={oid}" if oid else "tg://user?id=0"
    username_line = f"@{ouser}" if ouser else "—"

    text = (
        "**╭───⌁ معلومات المالك ⌁───⟤**\n"
        f"**│ ▸ الاسم:** [{oname}]({user_link})\n"
        f"**│ ▸ اليوزر:** {username_line}\n"
        f"**│ ▸ الآيدي:** `{oid}`\n"
        "**╰────────────────⟤**"
    )

    buttons = [[
        InlineKeyboardButton("✦ محادثة المالك ✦", url=user_link),
    ]]
    if ouser:
        buttons[0].append(InlineKeyboardButton("✧ يوزر ✧", url=f"https://t.me/{ouser}"))

    try:
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )
    except Exception:
        await message.reply_text(text, disable_web_page_preview=True)


# ═══════════════════════════════════════
# أمر: تغيير يوزر المالك
# ═══════════════════════════════════════
@Client.on_message(command2(["تغيير يوزر المالك", "تغيير المالك", "change_owner"]))
async def change_owner_cmd(client: Client, message: Message):
    if not message.from_user:
        return

    uid = message.from_user.id
    if not _is_real_owner(uid):
        return await message.reply_text(
            "• الأمر ده للمالك الرسمي / أصحاب البوت بس.\n"
            f"• آيدي حضرتك: <code>{uid}</code>"
        )

    key = (message.chat.id, uid)
    _pending[key] = {"await_target": True, "request_msg_id": message.id}

    await message.reply_text(
        "✏️ ابعت دلوقتي يوزر أو آيدي المالك الجديد.\n"
        "ممكن كمان ترد بالرسالة على المستخدم نفسه.\n"
        "اكتب «الغاء» للإلغاء.",
        reply_to_message_id=message.id,
    )


# ═══════════════════════════════════════
# أمر: تحديث / ارجاع المالك للمالك الرسمي
# ═══════════════════════════════════════
@Client.on_message(command2(["تحديث المالك", "ارجاع المالك", "إرجاع المالك", "reset_owner"]))
async def reset_owner_cmd(client: Client, message: Message):
    if not message.from_user:
        return

    uid = message.from_user.id
    if not _is_real_owner(uid):
        return await message.reply_text(
            "• الأمر ده للمالك الرسمي / أصحاب البوت بس.\n"
            f"• آيدي حضرتك: <code>{uid}</code>"
        )

    data = _load_state()
    data.pop("display_owner_id", None)
    data.pop("display_owner_username", None)
    data.pop("display_owner_name", None)
    _save_state(data)

    await message.reply_text(
        "✅ تم إرجاع المالك للمالك الرسمي.\n"
        f"• آيدي المالك الرسمي: <code>{int(OWNER_ID) if OWNER_ID else 0}</code>"
    )


# ═══════════════════════════════════════
# التقاط رسالة المالك الجديد
# ═══════════════════════════════════════
@Client.on_message(filters.text & ~filters.via_bot, group=51)
async def _capture_new_owner(client: Client, message: Message):
    if not message.from_user:
        return
    key = (message.chat.id, message.from_user.id)
    state = _pending.get(key)
    if not state or not state.get("await_target"):
        return

    if message.id == state.get("request_msg_id"):
        return

    text = (message.text or "").strip()
    target_id = None
    target_username = None
    target_name = None

    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        target_id = u.id
        target_username = u.username
        target_name = ((u.first_name or "") + ((" " + u.last_name) if u.last_name else "")).strip()
    else:
        if _is_command_like(text):
            _pending.pop(key, None)
            return
        if text.lower() in _CANCEL_WORDS:
            _pending.pop(key, None)
            return await message.reply_text("• تم الإلغاء.")

        cleaned = text.lstrip("@").strip()
        try:
            if cleaned.lstrip("-").isdigit():
                target_id = int(cleaned)
                try:
                    u = await client.get_users(target_id)
                    target_username = u.username
                    target_name = ((u.first_name or "") + ((" " + u.last_name) if u.last_name else "")).strip()
                except Exception:
                    pass
            else:
                u = await client.get_users(cleaned)
                target_id = u.id
                target_username = u.username
                target_name = ((u.first_name or "") + ((" " + u.last_name) if u.last_name else "")).strip()
        except Exception:
            _pending.pop(key, None)
            return await message.reply_text("• معرفتش أوصل للمستخدم ده. حاول تاني.")

    _pending.pop(key, None)

    data = _load_state()
    data["display_owner_id"] = target_id
    if target_username:
        data["display_owner_username"] = target_username
    else:
        data.pop("display_owner_username", None)
    if target_name:
        data["display_owner_name"] = target_name
    else:
        data.pop("display_owner_name", None)
    _save_state(data)

    name_show = target_name or (f"@{target_username}" if target_username else str(target_id))
    user_link = f"tg://user?id={target_id}"
    await message.reply_text(
        "✅ تم تعيين المالك الظاهر بنجاح.\n"
        f"• الاسم: [{name_show}]({user_link})\n"
        f"• اليوزر: {('@' + target_username) if target_username else '—'}\n"
        f"• الآيدي: `{target_id}`",
        disable_web_page_preview=True,
    )
