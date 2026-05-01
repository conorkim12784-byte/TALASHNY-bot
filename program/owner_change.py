"""
أمر «تغيير يوزر المالك»
- ينفذه: المالك الرسمي (OWNER_ID) وأصحاب البوت (SUDO_USERS) فقط
- المالك «الظاهر» اللي اتغير قبل كده مش يقدر يغيره (إلا لو هو سودو أصلاً)
- لما يتنفذ الأمر، البوت يطلب من اللي طلبه يبعت يوزر/آيدي المالك الجديد
- يستنى رسالة جديدة (مش يقرأ نص الأمر نفسه)
- يحفظ في owner_state.json
"""

import os
import json
from pyrogram import Client, filters
from pyrogram.types import Message

from driver.filters import command2

# استيراد آمن — كل قيمة لوحدها عشان لو واحدة ناقصة الباقي يفضل شغال
try:
    from config import SUDO_USERS  # type: ignore
except Exception:
    SUDO_USERS = []

try:
    from config import OWNER_ID  # type: ignore
except Exception:
    OWNER_ID = 0

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
    """يرجع SUDO_USERS كـ list of int بشكل آمن."""
    try:
        return [int(x) for x in (SUDO_USERS or [])]
    except Exception:
        try:
            return list(SUDO_USERS or [])
        except Exception:
            return []


def _is_real_owner(user_id: int) -> bool:
    """المالك الرسمي من config أو ضمن أصحاب البوت."""
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
    if first in {"تغيير", "المالك"}:
        return True
    return False


@Client.on_message(command2(["تغيير يوزر المالك", "تغيير المالك", "change_owner"]))
async def change_owner_cmd(client: Client, message: Message):
    if not message.from_user:
        return

    uid = message.from_user.id
    if not _is_real_owner(uid):
        # رسالة تشخيصية مفيدة
        return await message.reply_text(
            "• الأمر ده للمالك الرسمي / أصحاب البوت بس.\n"
            f"• آيدي حضرتك: <code>{uid}</code>\n"
            f"• أصحاب البوت الحاليين: <code>{_sudo_list()}</code>"
        )

    key = (message.chat.id, uid)
    _pending[key] = {"await_target": True, "request_msg_id": message.id}

    await message.reply_text(
        "✏️ ابعت دلوقتي يوزر أو آيدي المالك الجديد.\n"
        "ممكن كمان ترد بالرسالة على المستخدم نفسه.\n"
        "اكتب «الغاء» للإلغاء.",
        reply_to_message_id=message.id,
    )


@Client.on_message(filters.text & ~filters.via_bot, group=51)
async def _capture_new_owner(client: Client, message: Message):
    if not message.from_user:
        return
    key = (message.chat.id, message.from_user.id)
    state = _pending.get(key)
    if not state or not state.get("await_target"):
        return

    # تجاهل رسالة الأمر نفسها
    if message.id == state.get("request_msg_id"):
        return

    text = (message.text or "").strip()
    target_id = None
    target_username = None

    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        target_id = u.id
        target_username = u.username
    else:
        if _is_command_like(text):
            _pending.pop(key, None)
            return
        if text.lower() in _CANCEL_WORDS:
            _pending.pop(key, None)
            return await message.reply_text("• تم الإلغاء.")

        cleaned = text.lstrip("@").strip()
        if cleaned.isdigit():
            target_id = int(cleaned)
        else:
            try:
                user = await client.get_users(cleaned)
                target_id = user.id
                target_username = user.username
            except Exception:
                _pending.pop(key, None)
                return await message.reply_text("• معرفتش أوصل للمستخدم ده. حاول تاني.")

    _pending.pop(key, None)

    data = _load_state()
    data["display_owner_id"] = target_id
    if target_username:
        data["display_owner_username"] = target_username
    _save_state(data)

    await message.reply_text(
        f"✅ تم تعيين المالك الظاهر للآيدي: <code>{target_id}</code>",
    )


def get_display_owner_id() -> int:
    data = _load_state()
    try:
        return int(data.get("display_owner_id") or OWNER_ID or 0)
    except Exception:
        return 0
