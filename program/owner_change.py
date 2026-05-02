"""
أوامر المالك (لكل جروب على حدة):

- «المالك» / «مالك» / «owner»
    → في أي جروب: يعرض صاحب الجروب الفعلي (creator) من Telegram
      مع صورته واسمه ومنشن ماركداون. يقدر أي عضو يستخدمه.
    → لو صاحب البوت (SUDO_USERS) عيّن "مالك ظاهر" مخصّص للجروب ده،
      هيظهر هو بدل الـ creator، لحد ما يترجع.

- «تغيير يوزر المالك» / «تغيير المالك» / «change_owner»
    → لصاحب البوت بس. يغيّر المالك الظاهر للجروب الحالي فقط.

- «تحديث المالك» / «ارجاع المالك» / «reset_owner»
    → لصاحب البوت بس. يرجّع المالك الظاهر لصاحب الجروب الفعلي.

التخزين لكل جروب على حدة في owner_state.json
"""

import os
import json
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ChatType
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
    """صلاحية تغيير/إرجاع المالك مقصورة على SUDO_USERS بس."""
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
    if first in {"تغيير", "المالك", "تحديث", "ارجاع", "إرجاع"}:
        return True
    return False


# ═══════════════════════════════════════
# جلب صاحب الجروب الحقيقي من Telegram
# ═══════════════════════════════════════
async def _fetch_real_group_owner(client: Client, chat_id: int):
    """يرجع pyrogram User للـ creator الفعلي للجروب، أو None."""
    try:
        async for m in client.get_chat_members(
            chat_id, filter="administrators"
        ):
            try:
                if m.status == ChatMemberStatus.OWNER:
                    return m.user
            except Exception:
                # fallback لو الـ enum مختلف
                if str(getattr(m, "status", "")).lower().endswith("owner") or \
                   str(getattr(m, "status", "")).lower().endswith("creator"):
                    return m.user
    except Exception:
        pass
    return None


def _full_name(u) -> str:
    if not u:
        return "المالك"
    name = ((u.first_name or "") + ((" " + u.last_name) if u.last_name else "")).strip()
    return name or "المالك"


# ═══════════════════════════════════════
# أمر: عرض المالك (لكل الأعضاء)
# ═══════════════════════════════════════
@Client.on_message(command2(["المالك", "مالك", "owner"]))
async def show_owner_cmd(client: Client, message: Message):
    chat = message.chat
    # في الخاص: ما فيش "صاحب جروب"
    if chat.type == ChatType.PRIVATE:
        return await message.reply_text("• الأمر ده يستخدم داخل المجموعات بس.")

    chat_key = str(chat.id)
    state = _load_state().get(chat_key) or {}

    target_id = None
    target_user = None
    target_name = None
    target_username = None

    # 1) لو في مالك مخصّص للجروب ده — استخدمه (مع تحديث اليوزر/الاسم تلقائياً من تيليجرام)
    custom_id = state.get("display_owner_id")
    if custom_id:
        try:
            target_id = int(custom_id)
            try:
                target_user = await client.get_users(target_id)
                target_name = _full_name(target_user)
                target_username = target_user.username or ""
            except Exception:
                target_name = state.get("display_owner_name") or "المالك"
                target_username = state.get("display_owner_username") or ""
        except Exception:
            target_id = None

    # 2) غير كده — هات صاحب الجروب الفعلي
    if not target_id:
        real = await _fetch_real_group_owner(client, chat.id)
        if real:
            target_user = real
            target_id = real.id
            target_name = _full_name(real)
            target_username = real.username
        else:
            return await message.reply_text(
                "• معرفتش أوصل لصاحب المجموعة. اتأكد إن البوت مشرف."
            )

    # تحديث تلقائي: لو معندناش بيانات محفوظة، احفظ صاحب الجروب الفعلي
    # ولو اليوزر/الاسم اتغير من تيليجرام، حدّثهم تلقائياً
    try:
        if target_user is not None:
            data_all = _load_state()
            chat_state = data_all.get(chat_key) or {}
            fresh_username = target_user.username or ""
            fresh_name = _full_name(target_user)
            changed = False
            if chat_state.get("display_owner_id") != target_id:
                chat_state["display_owner_id"] = target_id
                changed = True
            if chat_state.get("display_owner_username", "") != fresh_username:
                if fresh_username:
                    chat_state["display_owner_username"] = fresh_username
                else:
                    chat_state.pop("display_owner_username", None)
                changed = True
            if chat_state.get("display_owner_name", "") != fresh_name:
                chat_state["display_owner_name"] = fresh_name
                changed = True
            if changed:
                data_all[chat_key] = chat_state
                _save_state(data_all)
                target_username = fresh_username
                target_name = fresh_name
    except Exception:
        pass

    # منشن ماركداون
    safe_name = (target_name or "المالك").replace("[", "(").replace("]", ")")
    mention_md = f"[{safe_name}](tg://user?id={target_id})"
    username_line = f"@{target_username}" if target_username else "—"

    caption = (
        "**╭───⌁ صاحب المجموعة ⌁───⟤**\n"
        f"**الاسم:** {mention_md}\n"
        f"**اليوزر:** {username_line}\n"
        f"**الآيدي:** `{target_id}`\n"
        "**╰────⌁ صاحب المجموعة ⌁────⟤**"
    )

    # نحاول نبعت صورة البروفايل
    photo_file_id = None
    try:
        async for ph in client.get_chat_photos(target_id, limit=1):
            photo_file_id = ph.file_id
            break
    except Exception:
        photo_file_id = None

    try:
        if photo_file_id:
            await message.reply_photo(
                photo=photo_file_id,
                caption=caption,
            )
        else:
            await message.reply_text(caption, disable_web_page_preview=True)
    except Exception:
        try:
            await message.reply_text(caption, disable_web_page_preview=True)
        except Exception:
            pass


# ═══════════════════════════════════════
# أمر: تغيير يوزر المالك (لصاحب البوت بس — لكل جروب على حدة)
# ═══════════════════════════════════════
@Client.on_message(command2(["تغيير يوزر المالك", "تغيير المالك", "change_owner"]))
async def change_owner_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply_text("• الأمر ده يستخدم داخل المجموعات بس.")

    uid = message.from_user.id
    if not _is_bot_owner(uid):
        return await message.reply_text(
            "• الأمر ده لصاحب البوت بس.\n"
            f"• آيدي حضرتك: <code>{uid}</code>"
        )

    key = (message.chat.id, uid)
    _pending[key] = {"await_target": True, "request_msg_id": message.id}

    await message.reply_text(
        "✏️ ابعت دلوقتي يوزر أو آيدي المالك الجديد للجروب ده.\n"
        "ممكن كمان ترد بالرسالة على المستخدم نفسه.\n"
        "اكتب «الغاء» للإلغاء.",
        reply_to_message_id=message.id,
    )


# ═══════════════════════════════════════
# أمر: ارجاع المالك لصاحب الجروب الحقيقي (لصاحب البوت بس)
# ═══════════════════════════════════════
@Client.on_message(command2(["تحديث المالك", "ارجاع المالك", "إرجاع المالك", "reset_owner"]))
async def reset_owner_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply_text("• الأمر ده يستخدم داخل المجموعات بس.")

    uid = message.from_user.id
    if not _is_bot_owner(uid):
        return await message.reply_text(
            "• الأمر ده لصاحب البوت بس.\n"
            f"• آيدي حضرتك: <code>{uid}</code>"
        )

    data = _load_state()
    chat_key = str(message.chat.id)
    if chat_key in data:
        data.pop(chat_key, None)
        _save_state(data)

    await message.reply_text(
        "✅ تم إرجاع المالك لصاحب المجموعة الفعلي."
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
        target_name = _full_name(u)
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
                    target_name = _full_name(u)
                except Exception:
                    pass
            else:
                u = await client.get_users(cleaned)
                target_id = u.id
                target_username = u.username
                target_name = _full_name(u)
        except Exception:
            _pending.pop(key, None)
            return await message.reply_text("• معرفتش أوصل للمستخدم ده. حاول تاني.")

    _pending.pop(key, None)

    data = _load_state()
    chat_key = str(message.chat.id)
    chat_state = data.get(chat_key) or {}
    chat_state["display_owner_id"] = target_id
    if target_username:
        chat_state["display_owner_username"] = target_username
    else:
        chat_state.pop("display_owner_username", None)
    if target_name:
        chat_state["display_owner_name"] = target_name
    else:
        chat_state.pop("display_owner_name", None)
    data[chat_key] = chat_state
    _save_state(data)

    name_show = target_name or (f"@{target_username}" if target_username else str(target_id))
    user_link = f"tg://user?id={target_id}"
    await message.reply_text(
        "✅ تم تعيين المالك الظاهر للجروب ده بنجاح.\n"
        f"• الاسم: [{name_show}]({user_link})\n"
        f"• اليوزر: {('@' + target_username) if target_username else '—'}\n"
        f"• الآيدي: `{target_id}`",
        disable_web_page_preview=True,
    )
