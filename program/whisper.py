"""
نظام الهمس (Whisper) — زي بوتات تليجرام الشهيرة.

طريقة الاستخدام (للأعضاء):
1) في أي شات اكتب اسم البوت + الرسالة بالشكل ده:
   @BotUsername @TargetUser رسالتك السرية
   أو ترد: @BotUsername بالرد على المستخدم — هتكتب بعدها الرسالة.
   مثال: @MyBot @ahmed أنا بحبك
2) البوت بيرجّع نتيجة Inline. اختار النتيجة وابعتها للجروب/الشات.
3) لما المستخدم المستهدف يدوس على «اقرأ الهمسة» تظهرله الرسالة في تنبيه
   خاص بيه فقط، أي حد تاني يدوس بيظهرله "الرسالة دي مش ليك".

التحكم (للمالك/المشرفين/أصحاب البوت):
- «تفعيل الهمس» / «تعطيل الهمس» / لوحة بأزرار Inline عبر «الهمس».

التخزين: ملف whisper_state.json (in-memory للرسائل + JSON لإعدادات الجروب).
"""

import os
import json
import uuid
from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from driver.filters import command2
from driver.permissions import get_rank

try:
    from config import SUDO_USERS
except Exception:
    SUDO_USERS = []


STATE_FILE = "whisper_state.json"

# in-memory store للرسائل: { whisper_id: {target_id, target_username, sender_id, text} }
# (ملاحظة: لو البوت اترستر هتضيع — ده طبيعي ومقبول للهمس)
_whispers: dict = {}


# ═══════════════════════════════════════════════
# تخزين تفعيل/تعطيل لكل جروب
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


def _is_enabled(chat_id: Optional[int]) -> bool:
    if chat_id is None:
        return True  # في الخاص الهمس مفتوح دائمًا
    data = _load()
    # default ON
    return bool(data.get(str(chat_id), {}).get("enabled", True))


def _set_enabled(chat_id: int, enabled: bool):
    data = _load()
    st = data.get(str(chat_id), {})
    st["enabled"] = enabled
    data[str(chat_id)] = st
    _save(data)


def _is_sudo(uid: int) -> bool:
    if not uid:
        return False
    try:
        return int(uid) in [int(x) for x in (SUDO_USERS or [])]
    except Exception:
        return False


# ═══════════════════════════════════════════════
# لوحة التحكم
# ═══════════════════════════════════════════════

def _panel_kb(chat_id: int) -> InlineKeyboardMarkup:
    enabled = _is_enabled(chat_id)
    txt = "🔴 تعطيل الهمسة" if enabled else "🟢 تفعيل الهمسة"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(txt, callback_data=f"wh:toggle:{chat_id}")],
        [InlineKeyboardButton("✖️ إغلاق", callback_data="wh:close")],
    ])


def _panel_text(chat_id: int) -> str:
    enabled = _is_enabled(chat_id)
    return (
        "**╭───⌁ نظام الهمسة ⌁───⟤**\n"
        f"**│ ▸ الحالة:** {'🟢 مفعّل' if enabled else '🔴 معطّل'}\n"
        "**│ ▸ الاستخدام:** اكتب في أي شات\n"
        "**│   `@BOT_USERNAME @user رسالتك`**\n"
        "**╰────────────────⟤**"
    )


@Client.on_message(command2(["همسة", "الهمسة", "الهمس", "همس", "whisper"]) & filters.group)
async def whisper_panel(client: Client, message: Message):
    if not message.from_user:
        return
    rank = await get_rank(client, message.chat.id, message.from_user.id)
    if rank not in ("admin", "owner", "sudo"):
        return await message.reply_text("• الأمر ده للمشرفين/المالك/أصحاب البوت بس.")
    await message.reply_text(_panel_text(message.chat.id), reply_markup=_panel_kb(message.chat.id))


@Client.on_message(command2(["تفعيل الهمسة", "تفعيل الهمس", "enable_whisper"]) & filters.group)
async def whisper_enable(client: Client, message: Message):
    if not message.from_user:
        return
    rank = await get_rank(client, message.chat.id, message.from_user.id)
    if rank not in ("admin", "owner", "sudo"):
        return await message.reply_text("• الأمر ده للمشرفين/المالك/أصحاب البوت بس.")
    _set_enabled(message.chat.id, True)
    await message.reply_text("✅ تم تفعيل نظام الهمسة في الجروب.")


@Client.on_message(command2(["تعطيل الهمسة", "تعطيل الهمس", "disable_whisper"]) & filters.group)
async def whisper_disable(client: Client, message: Message):
    if not message.from_user:
        return
    rank = await get_rank(client, message.chat.id, message.from_user.id)
    if rank not in ("admin", "owner", "sudo"):
        return await message.reply_text("• الأمر ده للمشرفين/المالك/أصحاب البوت بس.")
    _set_enabled(message.chat.id, False)
    await message.reply_text("🔴 تم تعطيل نظام الهمسة في الجروب.")


@Client.on_callback_query(filters.regex(r"^wh:"))
async def whisper_panel_cb(client: Client, cq: CallbackQuery):
    parts = cq.data.split(":")
    action = parts[1]
    if action == "close":
        try:
            await cq.message.delete()
        except Exception:
            pass
        return await cq.answer()
    if action == "toggle":
        chat_id = int(parts[2])
        rank = await get_rank(client, chat_id, cq.from_user.id)
        if rank not in ("admin", "owner", "sudo"):
            return await cq.answer("• مش ليك صلاحية.", show_alert=True)
        _set_enabled(chat_id, not _is_enabled(chat_id))
        try:
            await cq.message.edit_text(_panel_text(chat_id), reply_markup=_panel_kb(chat_id))
        except Exception:
            pass
        return await cq.answer("تم.")


# ═══════════════════════════════════════════════
# Inline Query لإنشاء همسة
# ═══════════════════════════════════════════════

@Client.on_inline_query()
async def whisper_inline(client: Client, query: InlineQuery):
    q = (query.query or "").strip()

    if not q:
        return await query.answer(
            results=[
                InlineQueryResultArticle(
                    title="نظام الهمسة 🔇",
                    description="اكتب: @user رسالتك السرية",
                    input_message_content=InputTextMessageContent(
                        "**نظام الهمسة**\n"
                        "الاستخدام: `@BotUsername @user رسالتك السرية`"
                    ),
                )
            ],
            cache_time=1,
            is_personal=True,
        )

    # توقع: "@username رسالة" أو "id رسالة"
    parts = q.split(None, 1)
    if len(parts) < 2:
        return await query.answer(
            results=[
                InlineQueryResultArticle(
                    title="❗ ناقص: اكتب اسم المستخدم ورسالة",
                    description="مثال: @ahmed أنا بحبك",
                    input_message_content=InputTextMessageContent(
                        "اكتب: `@username رسالتك السرية`"
                    ),
                )
            ],
            cache_time=1,
            is_personal=True,
        )

    target_raw, text = parts[0], parts[1]
    target_clean = target_raw.lstrip("@").strip()

    target_id = None
    target_username = None
    target_name = target_raw

    try:
        if target_clean.lstrip("-").isdigit():
            u = await client.get_users(int(target_clean))
        else:
            u = await client.get_users(target_clean)
        target_id = u.id
        target_username = u.username
        target_name = (u.first_name or "") + ((" " + u.last_name) if u.last_name else "")
        target_name = target_name.strip() or (u.username or str(u.id))
    except Exception:
        # نخزن باليوزر بس لو معرفناش الـ id — هنتعرف لما يدوس الزرار
        target_username = target_clean

    wid = uuid.uuid4().hex[:16]
    _whispers[wid] = {
        "target_id": target_id,
        "target_username": (target_username or "").lower(),
        "target_name": target_name,
        "sender_id": query.from_user.id,
        "sender_name": query.from_user.first_name or "",
        "text": text,
    }

    title = f"همسة لـ {target_name}"
    desc = "اضغط لإرسال رسالة سرية — تظهر له فقط."
    msg_text = (
        "**🔇 همسة سرية**\n"
        f"إلى: **{target_name}**\n"
        f"من: **{query.from_user.first_name or 'مجهول'}**\n\n"
        "اضغط على الزر تحت لقراءتها (للمستهدف فقط)."
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👁 اقرأ الهمسة", callback_data=f"wread:{wid}")]
    ])

    await query.answer(
        results=[
            InlineQueryResultArticle(
                id=wid,
                title=title,
                description=desc,
                input_message_content=InputTextMessageContent(msg_text),
                reply_markup=kb,
            )
        ],
        cache_time=1,
        is_personal=True,
    )


@Client.on_callback_query(filters.regex(r"^wread:"))
async def whisper_read_cb(client: Client, cq: CallbackQuery):
    wid = cq.data.split(":", 1)[1]
    w = _whispers.get(wid)
    if not w:
        return await cq.answer("⌛ الهمسة دي انتهت أو مش موجودة.", show_alert=True)

    uid = cq.from_user.id
    uname = (cq.from_user.username or "").lower()

    # تفعيل/تعطيل في الجروب
    chat = cq.message.chat if cq.message else None
    if chat and chat.type and str(chat.type).lower().endswith("group") and not _is_enabled(chat.id):
        return await cq.answer("• نظام الهمسة متعطّل في الجروب ده.", show_alert=True)

    is_target = False
    if w.get("target_id") and uid == w["target_id"]:
        is_target = True
    elif w.get("target_username") and uname and uname == w["target_username"]:
        is_target = True

    # السودو + المرسل ممكن يقروا برضه (اختياري — للمرسل بس)
    is_sender = uid == w.get("sender_id")

    if is_target:
        return await cq.answer(f"💬 {w.get('text','')}", show_alert=True)
    if is_sender:
        return await cq.answer(f"📝 (نسختك): {w.get('text','')}", show_alert=True)

    return await cq.answer("🚫 الهمسة دي مش ليك.", show_alert=True)
