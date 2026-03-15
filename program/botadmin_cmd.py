# botadmin_cmd.py

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from driver.filters import command, command2, other_filters
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
        return member.status.value == "owner"
    except Exception:
        return False


def _perms_to_keyboard(user_id: int, perms: set) -> InlineKeyboardMarkup:
    rows = []
    for key, label in ALL_PERMISSIONS.items():
        icon = "✅" if key in perms else "❌"
        rows.append([InlineKeyboardButton(
            f"{icon} {label}",
            callback_data=f"ba|{user_id}|{key}|{int(key in perms)}"
        )])
    rows.append([
        InlineKeyboardButton("✅ ارفعه دلوقتي", callback_data=f"ba_confirm|{user_id}"),
        InlineKeyboardButton("❌ الغاء", callback_data="ba_cancel"),
    ])
    return InlineKeyboardMarkup(rows)


def _extract_perms(markup) -> set:
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
@Client.on_message((command(["botadmin"]) | command2(["رفع بوت", "بوت ادمن", "رفع مدير", "رفع_مدير"])) & other_filters)
async def promote_bot_admin(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id

    if not await is_allowed(c, chat_id, m.from_user.id):
        return await m.reply("❌ مالك المجموعة بس")

    target = None
    if m.reply_to_message:
        target = m.reply_to_message.from_user
    elif len(m.command) >= 2:
        arg = m.command[1]
        try:
            target = await c.get_users(int(arg) if arg.isdigit() else arg)
        except Exception:
            return await m.reply("❌ مش لاقي المستخدم ده")

    if not target:
        return await m.reply("رد على المستخدم أو اكتب معرفه")
    if target.is_bot:
        return await m.reply("❌ مينفعش نرفع بوتات")
    if is_master(target.id):
        return await m.reply("👑 الواد ده فوق الكل أصلاً")

    current_perms = get_permissions(chat_id, target.id) or (set(ALL_PERMISSIONS.keys()) - {"promote"})
    keyboard = _perms_to_keyboard(target.id, current_perms)

    await m.reply(
        f"👤 **رفع بوت ادمن**\n\n"
        f"**المستخدم:** [{target.first_name}](tg://user?id={target.id})\n"
        f"**الايدي:** `{target.id}`\n\n"
        f"اختار الصلاحيات:",
        reply_markup=keyboard
    )


# ═══════════════════════════════════════
# شيل بوت ادمن
# ═══════════════════════════════════════
@Client.on_message((command(["rmbotadmin"]) | command2(["شيل بوت ادمن", "نزول بوت"])) & other_filters)
async def demote_bot_admin(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id

    if not await is_allowed(c, chat_id, m.from_user.id):
        return await m.reply("❌ مالك المجموعة بس")

    target = None
    if m.reply_to_message:
        target = m.reply_to_message.from_user
    elif len(m.command) >= 2:
        arg = m.command[1]
        try:
            target = await c.get_users(int(arg) if arg.isdigit() else arg)
        except Exception:
            return await m.reply("❌ مش لاقي المستخدم ده")

    if not target:
        return await m.reply("رد على المستخدم أو اكتب معرفه")

    if not is_bot_admin(chat_id, target.id):
        return await m.reply("❌ الشخص ده مش بوت ادمن أصلاً")

    remove_bot_admin(chat_id, target.id)
    await m.reply(f"✅ تم شيل [{target.first_name}](tg://user?id={target.id}) من البوت ادمنز")


# ═══════════════════════════════════════
# قايمة البوت ادمنز
# ═══════════════════════════════════════
@Client.on_message((command(["botadmins"]) | command2(["قايمة الادمنز", "بوت ادمنز"])) & other_filters)
async def list_bot_admins(c: Client, m: Message):
    await m.delete()
    admins = get_bot_admins(m.chat.id)
    if not admins:
        return await m.reply("❌ مفيش بوت ادمنز في الجروب ده")

    text = "**⚙️ البوت ادمنز:**\n\n"
    for user_id, perms in admins.items():
        try:
            user = await c.get_users(user_id)
            name = user.first_name
        except Exception:
            name = str(user_id)
        perms_text = ", ".join(ALL_PERMISSIONS.get(p, p) for p in perms)
        text += f"👤 [{name}](tg://user?id={user_id})\n» {perms_text}\n\n"

    await m.reply(text, disable_web_page_preview=True)


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

    perms = _extract_perms(query.message.reply_markup)
    if current:
        perms.discard(key)
    else:
        perms.add(key)

    await query.message.edit_reply_markup(_perms_to_keyboard(user_id, perms))
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

    perms = _extract_perms(query.message.reply_markup)
    add_bot_admin(chat_id, user_id, perms)
    target = await c.get_users(user_id)

    perms_text = "\n".join(
        f"  {'✅' if k in perms else '❌'} {v}"
        for k, v in ALL_PERMISSIONS.items()
    )

    await query.message.edit_text(
        f"✅ **تم الرفع بنجاح**\n\n"
        f"👤 **المستخدم:** [{target.first_name}](tg://user?id={user_id})\n"
        f"🏠 **المجموعة:** `{chat_id}`\n\n"
        f"**الصلاحيات:**\n{perms_text}"
    )
    await query.answer()


# ═══════════════════════════════════════
# callback الغاء
# ═══════════════════════════════════════
@Client.on_callback_query(filters.regex("^ba_cancel$"))
async def cancel_bot_admin(c: Client, query: CallbackQuery):
    await query.message.delete()
    await query.answer()
