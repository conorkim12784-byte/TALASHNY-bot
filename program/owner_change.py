"""
أوامر المالك لكل جروب:
- المالك / مالك / owner: يعرض صاحب الجروب الفعلي أو المالك الظاهر المخصص.
- تغيير يوزر المالك / تغيير المالك / change_owner: لصاحب البوت فقط.
- تحديث المالك / ارجاع المالك / reset_owner: تحديث صاحب الجروب الفعلي.
"""

import json
import os

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ChatType
try:
    from pyrogram.enums import ChatMembersFilter
except Exception:
    ChatMembersFilter = None  # type: ignore
from pyrogram.types import Message

from driver.filters import command2

try:
    from config import SUDO_USERS  # type: ignore
except Exception:
    SUDO_USERS = []

STATE_FILE = "owner_state.json"
_pending: dict = {}

_PREFIXES = ("/", "!", ".", "؟", "?", "#")
_CANCEL_WORDS = {"الغاء", "إلغاء", "كنسل", "cancel", "خلاص"}


def _load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
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


def _is_bot_owner(user_id: int) -> bool:
    if not user_id:
        return False
    try:
        return int(user_id) in _sudo_list()
    except Exception:
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
    return first in {"تغيير", "المالك", "تحديث", "ارجاع", "إرجاع"}


def _status_is_owner(status) -> bool:
    try:
        if status == ChatMemberStatus.OWNER:
            return True
    except Exception:
        pass
    value = getattr(status, "value", status)
    return str(value).lower() in ("creator", "owner") or str(value).lower().endswith(("owner", "creator"))


async def _fetch_real_group_owner(client: Client, chat_id: int):
    """يرجع User صاحب الجروب الفعلي حتى مع اختلاف إصدارات Pyrogram."""
    try:
        chat = await client.get_chat(chat_id)
        for attr in ("owner", "creator"):
            user = getattr(chat, attr, None)
            if user:
                return user
    except Exception:
        pass

    if ChatMembersFilter is not None:
        try:
            async for member in client.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
                if _status_is_owner(getattr(member, "status", None)):
                    return member.user
        except Exception:
            pass

    try:
        async for member in client.get_chat_members(chat_id):
            if _status_is_owner(getattr(member, "status", None)):
                return member.user
    except Exception:
        pass

    try:
        async for member in client.get_chat_members(chat_id, filter="administrators"):
            if _status_is_owner(getattr(member, "status", None)):
                return member.user
    except Exception:
        pass

    return None


def _full_name(user) -> str:
    if not user:
        return "المالك"
    first = getattr(user, "first_name", None) or ""
    last = getattr(user, "last_name", None) or ""
    username = getattr(user, "username", None) or ""
    name = (first + ((" " + last) if last else "")).strip()
    return name or (f"@{username}" if username else "المالك")


def _save_owner_cache(chat_id: int, user, is_custom: bool) -> None:
    if not user:
        return
    data = _load_state()
    chat_key = str(chat_id)
    chat_state = data.get(chat_key) or {}
    chat_state["display_owner_id"] = int(user.id)
    chat_state["display_owner_name"] = _full_name(user)
    chat_state["is_custom_owner"] = bool(is_custom)
    username = getattr(user, "username", None) or ""
    if username:
        chat_state["display_owner_username"] = username
    else:
        chat_state.pop("display_owner_username", None)
    data[chat_key] = chat_state
    _save_state(data)


async def refresh_group_owner_state(client: Client, chat_id: int):
    """يحدّث المالك الفعلي في التخزين ويرجع User أو None."""
    real = await _fetch_real_group_owner(client, chat_id)
    if real:
        _save_owner_cache(chat_id, real, is_custom=False)
    return real


@Client.on_message(command2(["المالك", "مالك", "owner"]))
async def show_owner_cmd(client: Client, message: Message):
    chat = message.chat
    if chat.type == ChatType.PRIVATE:
        return await message.reply_text("الأمر ده يستخدم داخل المجموعات بس.")

    chat_key = str(chat.id)
    state = _load_state().get(chat_key) or {}

    target_id = None
    target_user = None
    target_name = None
    target_username = None
    using_custom = False

    custom_id = state.get("display_owner_id") if state.get("is_custom_owner") else None
    if custom_id:
        try:
            target_id = int(custom_id)
            using_custom = True
            try:
                target_user = await client.get_users(target_id)
                target_name = _full_name(target_user)
                target_username = target_user.username or ""
            except Exception:
                target_name = state.get("display_owner_name") or "المالك"
                target_username = state.get("display_owner_username") or ""
        except Exception:
            target_id = None
            using_custom = False

    if not target_id:
        real = await _fetch_real_group_owner(client, chat.id)
        if real:
            target_user = real
            target_id = real.id
            target_name = _full_name(real)
            target_username = real.username or ""
            using_custom = False
        else:
            return await message.reply_text("معرفتش أوصل لصاحب المجموعة. اتأكد إن البوت مشرف وعنده صلاحية رؤية المشرفين.")

    try:
        if target_user is not None:
            _save_owner_cache(chat.id, target_user, is_custom=using_custom)
            target_name = _full_name(target_user)
            target_username = target_user.username or ""
    except Exception:
        pass

    username_line = f"@{target_username}" if target_username else "لا يوجد"
    caption = (
        "صاحب المجموعة\n"
        f"الاسم: {target_name or 'المالك'}\n"
        f"اليوزر: {username_line}\n"
        f"الآيدي: {target_id}"
    )

    photo_file_id = None
    try:
        async for photo in client.get_chat_photos(target_id, limit=1):
            photo_file_id = photo.file_id
            break
    except Exception:
        photo_file_id = None

    try:
        if photo_file_id:
            await message.reply_photo(photo=photo_file_id, caption=caption)
        else:
            await message.reply_text(caption, disable_web_page_preview=True)
    except Exception:
        try:
            await message.reply_text(caption, disable_web_page_preview=True)
        except Exception:
            pass


@Client.on_message(command2(["تغيير يوزر المالك", "تغيير المالك", "change_owner"]))
async def change_owner_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply_text("الأمر ده يستخدم داخل المجموعات بس.")

    uid = message.from_user.id
    if not _is_bot_owner(uid):
        return await message.reply_text(f"الأمر ده لصاحب البوت بس.\nآيدي حضرتك: {uid}")

    key = (message.chat.id, uid)
    _pending[key] = {"await_target": True, "request_msg_id": message.id}

    await message.reply_text(
        "ابعت يوزر أو آيدي المالك الجديد للجروب ده.\n"
        "ممكن كمان ترد بالرسالة على المستخدم نفسه.\n"
        "اكتب الغاء للإلغاء.",
        reply_to_message_id=message.id,
    )


@Client.on_message(command2(["تحديث المالك", "ارجاع المالك", "إرجاع المالك", "reset_owner"]))
async def reset_owner_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply_text("الأمر ده يستخدم داخل المجموعات بس.")

    uid = message.from_user.id
    if not _is_bot_owner(uid):
        return await message.reply_text(f"الأمر ده لصاحب البوت بس.\nآيدي حضرتك: {uid}")

    real = await refresh_group_owner_state(client, message.chat.id)
    if not real:
        return await message.reply_text("معرفتش أحدث صاحب المجموعة. اتأكد إن البوت مشرف وعنده صلاحية رؤية المشرفين.")

    await message.reply_text("تم تحديث المالك لصاحب المجموعة الفعلي.")


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
        user = message.reply_to_message.from_user
        target_id = user.id
        target_username = user.username or ""
        target_name = _full_name(user)
    else:
        if _is_command_like(text):
            _pending.pop(key, None)
            return
        if text.lower() in _CANCEL_WORDS:
            _pending.pop(key, None)
            return await message.reply_text("تم الإلغاء.")

        cleaned = text.lstrip("@").strip()
        try:
            if cleaned.lstrip("-").isdigit():
                target_id = int(cleaned)
                try:
                    user = await client.get_users(target_id)
                    target_username = user.username or ""
                    target_name = _full_name(user)
                except Exception:
                    target_name = str(target_id)
            else:
                user = await client.get_users(cleaned)
                target_id = user.id
                target_username = user.username or ""
                target_name = _full_name(user)
        except Exception:
            _pending.pop(key, None)
            return await message.reply_text("معرفتش أوصل للمستخدم ده. حاول تاني.")

    _pending.pop(key, None)

    data = _load_state()
    chat_key = str(message.chat.id)
    chat_state = data.get(chat_key) or {}
    chat_state["display_owner_id"] = int(target_id)
    chat_state["display_owner_name"] = target_name or str(target_id)
    chat_state["is_custom_owner"] = True
    if target_username:
        chat_state["display_owner_username"] = target_username
    else:
        chat_state.pop("display_owner_username", None)
    data[chat_key] = chat_state
    _save_state(data)

    await message.reply_text(
        "تم تعيين المالك الظاهر للجروب ده بنجاح.\n"
        f"الاسم: {target_name or target_id}\n"
        f"اليوزر: {('@' + target_username) if target_username else 'لا يوجد'}\n"
        f"الآيدي: {target_id}",
        disable_web_page_preview=True,
    )
