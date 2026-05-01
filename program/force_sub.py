"""
نظام الاشتراك الإجباري (Force Subscribe).

المزايا:
- تفعيل/تعطيل لكل جروب على حدة بأزرار Inline (للمالك/أصحاب البوت فقط).
- ضبط القناة/الجروب المطلوب الاشتراك فيه عبر أمر «ضبط قناة الاشتراك».
- فحص أوتوماتيك مع كل رسالة عبر getChatMember.
- لو العضو مش مشترك:
    • تتحذف رسالته فورًا.
    • تتحذف رسالة التنبيه السابقة (لو موجودة).
    • تتبعت رسالة جديدة فيها منشن باسم العضو [first_name](tg://user?id=...)
      + اسم القناة + زرار "اشتراك" + زرار "تم الاشتراك ✅" للتحقق اليدوي.
- الفحص بيتم كذلك أوتوماتيك مع كل رسالة جديدة بدون لمس الأزرار.

التخزين: ملف JSON محلي (force_sub_state.json).
"""

import os
import json
import asyncio
from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatMemberUpdated,
)
from pyrogram.errors import (
    UserNotParticipant,
    ChatAdminRequired,
    PeerIdInvalid,
    MessageDeleteForbidden,
)

from driver.filters import command2

try:
    from config import SUDO_USERS
except Exception:
    SUDO_USERS = []

try:
    from config import OWNER_ID
except Exception:
    try:
        OWNER_ID = int(SUDO_USERS[0]) if SUDO_USERS else 0
    except Exception:
        OWNER_ID = 0


STATE_FILE = "force_sub_state.json"

# pending state لضبط قناة الاشتراك
_pending_set: dict = {}

# ذاكرة آخر رسالة تنبيه لكل (chat_id, user_id) عشان نحذفها قبل الجديدة
_last_warn: dict = {}


# ═══════════════════════════════════════════════
# تخزين
# ═══════════════════════════════════════════════

def _load() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _get_chat_state(chat_id: int) -> dict:
    data = _load()
    return data.get(str(chat_id), {})


def _set_chat_state(chat_id: int, st: dict) -> None:
    data = _load()
    data[str(chat_id)] = st
    _save(data)


# ═══════════════════════════════════════════════
# صلاحيات
# ═══════════════════════════════════════════════

def _is_sudo(uid: int) -> bool:
    if not uid:
        return False
    try:
        return int(uid) in [int(x) for x in (SUDO_USERS or [])] or (OWNER_ID and int(uid) == int(OWNER_ID))
    except Exception:
        return False


# ═══════════════════════════════════════════════
# لوحة التحكم
# ═══════════════════════════════════════════════

def _panel_kb(chat_id: int) -> InlineKeyboardMarkup:
    st = _get_chat_state(chat_id)
    enabled = st.get("enabled", False)
    target = st.get("target_username") or st.get("target_chat_id") or "—"
    toggle_text = "🔴 تعطيل الاشتراك الإجباري" if enabled else "🟢 تفعيل الاشتراك الإجباري"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_text, callback_data=f"fsub:toggle:{chat_id}")],
        [InlineKeyboardButton(f"⚙️ ضبط القناة ({target})", callback_data=f"fsub:setch:{chat_id}")],
        [InlineKeyboardButton("✖️ إغلاق", callback_data="fsub:close")],
    ])


def _panel_text(chat_id: int) -> str:
    st = _get_chat_state(chat_id)
    enabled = st.get("enabled", False)
    target = st.get("target_username") or st.get("target_chat_id") or "—"
    return (
        "**╭───⌁ الاشتراك الإجباري ⌁───⟤**\n"
        f"**│ ▸ الحالة:** {'🟢 مفعّل' if enabled else '🔴 معطّل'}\n"
        f"**│ ▸ القناة:** `{target}`\n"
        "**╰────────────────⟤**\n"
        "اختار من الأزرار اللي تحت."
    )


@Client.on_message(
    command2([
        "اشتراك اجباري", "الاشتراك الاجباري",
        "اشتراك إجباري", "الاشتراك الإجباري",
        "force_sub", "fsub",
    ])
    & filters.group
)
async def fsub_panel(client: Client, message: Message):
    if not message.from_user or not _is_sudo(message.from_user.id):
        return await message.reply_text("• الأمر ده لأصحاب البوت / المالك بس.")
    await message.reply_text(
        _panel_text(message.chat.id),
        reply_markup=_panel_kb(message.chat.id),
    )


@Client.on_callback_query(filters.regex(r"^fsub:"))
async def fsub_cb(client: Client, cq: CallbackQuery):
    parts = cq.data.split(":")
    action = parts[1] if len(parts) > 1 else ""

    if action == "close":
        try:
            await cq.message.delete()
        except Exception:
            pass
        return await cq.answer()

    if action == "verify":
        # تحقق يدوي من اشتراك العضو
        chat_id = int(parts[2])
        target_user = int(parts[3])
        if cq.from_user.id != target_user:
            return await cq.answer("الزر ده ليك إنت بس.", show_alert=True)
        ok = await _is_subscribed(client, chat_id, target_user)
        if ok:
            _last_warn.pop((chat_id, target_user), None)
            try:
                await cq.message.delete()
            except Exception:
                pass
            return await cq.answer("✅ تمام، إنت مشترك. اتفضل.", show_alert=True)
        return await cq.answer("لسه مش لاقيك مشترك في القناة. اشترك الأول.", show_alert=True)

    # العمليات اللي تحت محتاجة صلاحية sudo
    if not _is_sudo(cq.from_user.id):
        return await cq.answer("• الأزرار دي للمالك/أصحاب البوت بس.", show_alert=True)

    chat_id = int(parts[2])

    if action == "toggle":
        st = _get_chat_state(chat_id)
        st["enabled"] = not st.get("enabled", False)
        _set_chat_state(chat_id, st)
        try:
            await cq.message.edit_text(
                _panel_text(chat_id),
                reply_markup=_panel_kb(chat_id),
            )
        except Exception:
            pass
        return await cq.answer(
            "✅ تم التفعيل" if st["enabled"] else "🔴 تم التعطيل",
            show_alert=False,
        )

    if action == "setch":
        _pending_set[(chat_id, cq.from_user.id)] = True
        await cq.answer()
        return await cq.message.reply_text(
            "✏️ ابعت يوزر القناة/الجروب (مثلاً @MyChannel) أو الآيدي.\n"
            "ملحوظة: لازم البوت يكون مشرف في القناة عشان يقدر يتأكد من الاشتراك.\n"
            "اكتب «الغاء» للإلغاء."
        )


# ═══════════════════════════════════════════════
# أمر سريع لضبط القناة
# ═══════════════════════════════════════════════

@Client.on_message(
    command2(["ضبط قناة الاشتراك", "ضبط الاشتراك", "set_fsub_channel"])
    & filters.group
)
async def set_fsub_channel_cmd(client: Client, message: Message):
    if not message.from_user or not _is_sudo(message.from_user.id):
        return await message.reply_text("• الأمر ده لأصحاب البوت / المالك بس.")
    parts = (message.text or "").split(None, 1)
    if len(parts) < 2:
        _pending_set[(message.chat.id, message.from_user.id)] = True
        return await message.reply_text(
            "✏️ ابعت يوزر القناة/الجروب أو الآيدي. اكتب «الغاء» للإلغاء."
        )
    await _apply_target(client, message, parts[1].strip())


@Client.on_message(filters.text & filters.group & ~filters.via_bot, group=52)
async def _capture_target(client: Client, message: Message):
    if not message.from_user:
        return
    key = (message.chat.id, message.from_user.id)
    if not _pending_set.get(key):
        return
    text = (message.text or "").strip()
    if text in ("الغاء", "إلغاء", "cancel"):
        _pending_set.pop(key, None)
        return await message.reply_text("• تم الإلغاء.")
    if text.startswith(("/", "!", ".")):
        return  # سيب الأمر يتم
    _pending_set.pop(key, None)
    await _apply_target(client, message, text)


async def _apply_target(client: Client, message: Message, raw: str):
    raw = raw.strip().lstrip("@")
    target_username = None
    target_chat_id = None
    title = raw
    invite_url = None

    try:
        if raw.lstrip("-").isdigit():
            ch = await client.get_chat(int(raw))
        else:
            ch = await client.get_chat(raw)
        target_chat_id = ch.id
        target_username = ch.username
        title = ch.title or raw
        try:
            invite_url = ch.invite_link
        except Exception:
            invite_url = None
        if not invite_url and target_username:
            invite_url = f"https://t.me/{target_username}"
    except Exception:
        return await message.reply_text(
            "• معرفتش أوصل للقناة دي. تأكد إنها صحيحة وإن البوت مشرف فيها."
        )

    # التحقق إن البوت مشرف
    try:
        me = await client.get_me()
        m = await client.get_chat_member(target_chat_id, me.id)
        status = getattr(m.status, "value", str(m.status)).lower()
        if status not in ("administrator", "creator", "owner"):
            return await message.reply_text(
                "• لازم البوت يكون مشرف في القناة دي عشان يقدر يتأكد من الاشتراك.\n"
                "ضيفه كمشرف وبعدين جرّب تاني."
            )
    except Exception:
        return await message.reply_text(
            "• البوت مش مشرف في القناة دي أو معرفش يوصلها."
        )

    st = _get_chat_state(message.chat.id)
    st["target_chat_id"] = target_chat_id
    st["target_username"] = target_username or ""
    st["target_title"] = title
    st["invite_url"] = invite_url or (f"https://t.me/{target_username}" if target_username else "")
    _set_chat_state(message.chat.id, st)

    await message.reply_text(
        f"✅ تم ضبط قناة الاشتراك الإجباري:\n"
        f"• الاسم: **{title}**\n"
        f"• اليوزر: {('@' + target_username) if target_username else '—'}\n"
        f"• الآيدي: `{target_chat_id}`"
    )


# ═══════════════════════════════════════════════
# الفحص الأوتوماتيك مع كل رسالة
# ═══════════════════════════════════════════════

async def _is_subscribed(client: Client, target_chat_id: int, user_id: int) -> bool:
    try:
        m = await client.get_chat_member(target_chat_id, user_id)
        status = getattr(m.status, "value", str(m.status)).lower()
        return status in ("member", "administrator", "creator", "owner", "restricted")
    except UserNotParticipant:
        return False
    except Exception:
        # لو في خطأ نوع آخر — نسيب العضو يعدّي عشان مانعملش false positives
        return True


@Client.on_message(filters.group & ~filters.service & ~filters.via_bot, group=5)
async def _force_sub_check(client: Client, message: Message):
    if not message.from_user:
        return
    uid = message.from_user.id
    chat_id = message.chat.id

    # سيبه يعدّي للمالك/أصحاب البوت
    if _is_sudo(uid):
        return

    st = _get_chat_state(chat_id)
    if not st.get("enabled"):
        return
    target_id = st.get("target_chat_id")
    if not target_id:
        return

    # لا نتدخل في أوامر الإدارة الخاصة بالاشتراك نفسه عشان نسمح بضبطه
    text = (message.text or "").strip()
    if text and text.split()[0] in {"ضبط", "اشتراك", "الاشتراك", "fsub"}:
        return

    # تخطّي المشرفين العاديين في الجروب
    try:
        m = await client.get_chat_member(chat_id, uid)
        s = getattr(m.status, "value", str(m.status)).lower()
        if s in ("administrator", "creator", "owner"):
            return
    except Exception:
        pass

    if await _is_subscribed(client, target_id, uid):
        return

    # غير مشترك → نحذف رسالته
    try:
        await message.delete()
    except (MessageDeleteForbidden, ChatAdminRequired):
        # البوت مش مشرف هنا — نسيب الموضوع
        return
    except Exception:
        pass

    # نحذف رسالة التنبيه السابقة (لو موجودة)
    prev = _last_warn.get((chat_id, uid))
    if prev:
        try:
            await client.delete_messages(chat_id, prev)
        except Exception:
            pass

    # نبعت تنبيه جديد
    first_name = (message.from_user.first_name or "صديقي").replace("[", "").replace("]", "")
    mention = f"[{first_name}](tg://user?id={uid})"
    title = st.get("target_title") or "القناة"
    invite_url = st.get("invite_url") or (
        f"https://t.me/{st.get('target_username')}" if st.get("target_username") else ""
    )

    buttons = []
    if invite_url:
        buttons.append([InlineKeyboardButton(f"📢 اشترك في {title}", url=invite_url)])
    buttons.append([InlineKeyboardButton("✅ تم الاشتراك", callback_data=f"fsub:verify:{target_id}:{uid}")])

    try:
        sent = await client.send_message(
            chat_id,
            f"**🚫 يا {mention}**\n"
            f"عشان تقدر تكتب في الجروب لازم تشترك الأول في **{title}**.\n"
            f"بعد ما تشترك دوس على «✅ تم الاشتراك».",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )
        _last_warn[(chat_id, uid)] = sent.id
    except Exception:
        pass

    # نوقف معالجة الرسالة دي بأي handler تاني
    message.stop_propagation() if hasattr(message, "stop_propagation") else None
