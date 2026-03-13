# botadmin_cmd.py — أوامر رفع وإدارة بوت ادمنز مع أزرار زرقاء

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from driver.filters import command, command2, other_filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from driver.botadmin import (
    ALL_PERMISSIONS, MASTER_ID,
    is_master, is_bot_admin,
    add_bot_admin, remove_bot_admin,
    get_bot_admins, get_permissions
)


async def is_allowed(c, chat_id, user_id):
    if is_master(user_id):
        return True
    try:
        member = await c.get_chat_member(chat_id, user_id)
        return member.status.value == "creator"
    except Exception:
        return False


def _perms_to_rows(user_id: int, perms: set) -> list:
    rows = []
    for key, label in ALL_PERMISSIONS.items():
        icon = "✅" if key in perms else "❌"
        rows.append([{
            "text": f"{icon} {label}",
            "callback_data": f"ba|{user_id}|{key}|{int(key in perms)}",
            "style": "primary"
        }])
    rows.append([
        {"text": "✅ ارفعه دلوقتي", "callback_data": f"ba_confirm|{user_id}", "style": "primary"},
        {"text": "❌ الغاء", "callback_data": "ba_cancel", "style": "primary"},
    ])
    return rows


def _rows_to_perms(inline_keyboard) -> set:
    """استخراج الصلاحيات من أزرار الرسالة"""
    perms = set()
    for row in inline_keyboard:
        for btn in row:
            cb = btn.get("callback_data", "") if isinstance(btn, dict) else getattr(btn, "callback_data", "")
            if cb and cb.startswith("ba|"):
                parts = cb.split("|")
                if len(parts) >= 4 and bool(int(parts[3])):
                    perms.add(parts[2])
    return perms


def _pyrogram_rows_to_perms(markup) -> set:
    """استخراج الصلاحيات من pyrogram InlineKeyboardMarkup"""
    perms = set()
    if not markup:
        return perms
    for row in markup.inline_keyboard:
        for btn in row:
            if btn.callback_data and btn.callback_data.startswith("ba|"):
                p = btn.callback_data.split("|")
                if len(p) >= 4 and bool(int(p[3])):
                    perms.add(p[2])
    return perms


# ═══════════════════════════════════════
# رفع بوت ادمن
# ═══════════════════════════════════════
@Client.on_message((command(["botadmin"]) | command2(["رفع بوت", "بوت ادمن", "ادمن بوت"])) & other_filters)
async def promote_bot_admin(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id

    if not await is_allowed(c, chat_id, m.from_user.id):
        return await m.reply("❌ الامر ده لمالك المجموعة بس")

    target = None
    if m.reply_to_message:
        target = m.reply_to_message.from_user
    elif len(m.command) >= 2:
        arg = m.command[1]
        try:
            target = await c.get_users(int(arg) if arg.lstrip("-").isdigit() else arg)
        except Exception:
            return await m.reply("❌ مش لاقي المستخدم ده")
    else:
        return await m.reply(
            "**الاستخدام:**\n"
            "» رد على مستخدم: `رفع بوت`\n"
            "» بالمعرف: `رفع بوت @username`\n"
            "» بالايدي: `رفع بوت 123456789`"
        )

    if not target:
        return await m.reply("❌ مش عارف اتعرف على المستخدم ده")
    if target.is_bot:
        return await m.reply("❌ مينفعش نرفع بوتات")
    if is_master(target.id):
        return await m.reply("👑 الواد ده فوق الكل اصلا")

    current_perms = get_permissions(chat_id, target.id)
    if not current_perms:
        current_perms = set(ALL_PERMISSIONS.keys()) - {"promote"}

    rows = _perms_to_rows(target.id, current_perms)
    await send_blue(
        chat_id,
        f"👤 **رفع بوت ادمن**\n\n"
        f"**المستخدم:** [{target.first_name}](tg://user?id={target.id})\n"
        f"**الايدي:** `{target.id}`\n\n"
        f"اختار الصلاحيات:",
        rows
    )


# ═══════════════════════════════════════
# callback تبديل صلاحية
# ═══════════════════════════════════════
@Client.on_callback_query(filters.regex(r"^ba\|"))
async def toggle_bot_perm(c: Client, query: CallbackQuery):
    if not await is_allowed(c, query.message.chat.id, query.from_user.id):
        return await query.answer("❌ مالك المجموعة بس", show_alert=True)

    parts = query.data.split("|")
    user_id = int(parts[1])
    key = parts[2]
    current = bool(int(parts[3]))

    perms = _pyrogram_rows_to_perms(query.message.reply_markup)
    if current:
        perms.discard(key)
    else:
        perms.add(key)

    rows = _perms_to_rows(user_id, perms)
    await edit_blue(query.message.chat.id, query.message.id, query.message.text, rows)
    await query.answer()


# ═══════════════════════════════════════
# callback تأكيد الرفع
# ═══════════════════════════════════════
@Client.on_callback_query(filters.regex(r"^ba_confirm\|"))
async def confirm_bot_admin(c: Client, query: CallbackQuery):
    if not await is_allowed(c, query.message.chat.id, query.from_user.id):
        return await query.answer("❌ مالك المجموعة بس", show_alert=True)

    user_id = int(query.data.split("|")[1])
    chat_id = query.message.chat.id

    perms = _pyrogram_rows_to_perms(query.message.reply_markup)
    add_bot_admin(chat_id, user_id, perms)
    target = await c.get_users(user_id)

    perms_text = "\n".join(
        f"  {'✅' if k in perms else '❌'} {v}"
        for k, v in ALL_PERMISSIONS.items()
    )

    await edit_blue(
        chat_id, query.message.id,
        f"✅ **تم الرفع بنجاح**\n\n"
        f"👤 **المستخدم:** [{target.first_name}](tg://user?id={user_id})\n"
        f"🏠 **المجموعة:** `{chat_id}`\n\n"
        f"**الصلاحيات:**\n{perms_text}",
        []
    )


# ═══════════════════════════════════════
# callback الغاء
# ═══════════════════════════════════════
@Client.on_callback_query(filters.regex("^ba_cancel$"))
async def cancel_bot_admin(c: Client, query: CallbackQuery):
    await query.message.delete()
    await query.answer()


# ═══════════════════════════════════════
# نزول بوت ادمن
# ═══════════════════════════════════════
@Client.on_message((command(["rmbotadmin"]) | command2(["شيل بوت ادمن", "نزول بوت"])) & other_filters)
async def demote_bot_admin(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id

    if not await is_allowed(c, chat_id, m.from_user.id):
        return await m.reply("❌ الامر ده لمالك المجموعة بس")

    target = None
    if m.reply_to_message:
        target = m.reply_to_message.from_user
    elif len(m.command) >= 2:
        arg = m.command[1]
        try:
            target = await c.get_users(int(arg) if arg.lstrip("-").isdigit() else arg)
        except Exception:
            return await m.reply("❌ مش لاقي المستخدم ده")
    else:
        return await m.reply("» رد على المستخدم او ابعت معرفه")

    if not target:
        return await m.reply("❌ مش عارف اتعرف على المستخدم ده")
    if not is_bot_admin(chat_id, target.id):
        return await m.reply("❌ الواد ده مش بوت ادمن اصلا")

    remove_bot_admin(chat_id, target.id)
    await m.reply(f"✅ [{target.first_name}](tg://user?id={target.id}) اتشال من البوت ادمنز")


# ═══════════════════════════════════════
# قايمة البوت ادمنز
# ═══════════════════════════════════════
@Client.on_message((command(["botadmins"]) | command2(["قايمة الادمنز", "بوت ادمنز"])) & other_filters)
async def list_bot_admins(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    admins = get_bot_admins(chat_id)

    if not admins:
        return await m.reply("📋 مفيش بوت ادمنز في الجروب ده")

    text = "📋 **بوت ادمنز الجروب:**\n\n"
    for uid, perms in admins.items():
        try:
            user = await c.get_users(uid)
            name = user.first_name
        except Exception:
            name = str(uid)
        perms_names = " | ".join(ALL_PERMISSIONS.get(p, p) for p in perms) or "بدون صلاحيات"
        text += f"👤 [{name}](tg://user?id={uid})\n└ {perms_names}\n\n"

    await m.reply(text)
