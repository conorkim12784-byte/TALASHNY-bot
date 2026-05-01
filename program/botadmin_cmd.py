# program/botadmin_cmd.py
# أوامر "المدير" (Manager) — صلاحيات داخل البوت.
#
# قواعد صارمة:
#   • رفع/تنزيل مدير = مسموح بس لـ:
#       - المالك الرسمي (MASTER_ID)
#       - أصحاب البوت (SUDO_USERS)
#       - مدير عنده صلاحية "promote_managers" بشكل صريح
#     (مالك الجروب بحد ذاته **لا يكفي**؛ لازم يكون من اللي فوق).
#
#   • أزرار الصلاحيات بتولّد تلقائيًا من ALL_PERMISSIONS (auto-discover)،
#     فأي أمر جديد بيتضاف لفئة موجودة بيتغطى تلقائيًا.
#
#   • زرار "تفعيل الكل" و "تعطيل الكل" للسرعة.
#
#   • مدير عنده promote_managers مش مسموح يدّي صلاحيات RESTRICTED_PERMISSIONS
#     (زي manage_bot) — دي بس من المالك/السوبر.

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from driver.filters import command, command2, other_filters
from driver.botadmin import (
    ALL_PERMISSIONS, RESTRICTED_PERMISSIONS, MASTER_ID,
    is_master, is_bot_admin, can_promote_managers,
    add_bot_admin, remove_bot_admin,
    get_bot_admins, get_permissions,
)


# ════════════════════════════════════════════════════
# التحقق من الصلاحية لرفع/تنزيل مدير
# ════════════════════════════════════════════════════
async def can_manage_managers(c: Client, chat_id: int, user_id: int) -> bool:
    """
    مين مسموح له يرفع/ينزّل مديرين:
      • المالك الرسمي
      • أصحاب البوت (SUDO)
      • مدير عنده صلاحية promote_managers
    """
    if is_master(user_id):
        return True
    if can_promote_managers(chat_id, user_id):
        return True
    return False


def _allowed_perms_for(actor_id: int, chat_id: int) -> set:
    """
    الصلاحيات اللي الـ actor مسموح يمنحها.
    المالك/السوبر = كل حاجة.
    المدير صاحب promote_managers = كل حاجة ما عدا RESTRICTED_PERMISSIONS.
    """
    if is_master(actor_id):
        return set(ALL_PERMISSIONS.keys())
    return set(ALL_PERMISSIONS.keys()) - RESTRICTED_PERMISSIONS


# ════════════════════════════════════════════════════
# بناء كيبورد الصلاحيات (auto من ALL_PERMISSIONS)
# ════════════════════════════════════════════════════
def _perms_to_keyboard(actor_id: int, target_id: int, chat_id: int, perms: set) -> InlineKeyboardMarkup:
    allowed = _allowed_perms_for(actor_id, chat_id)
    rows = []
    # زرّين فوق: تفعيل/تعطيل الكل
    rows.append([
        InlineKeyboardButton("✔ تفعيل الكل", callback_data=f"ba_all|{actor_id}|{target_id}|1"),
        InlineKeyboardButton("✘ تعطيل الكل", callback_data=f"ba_all|{actor_id}|{target_id}|0"),
    ])

    # كل الصلاحيات — اللي مش مسموحة للـ actor تظهر بـ 🔒 ومُعطّلة فعليًا
    for key, label in ALL_PERMISSIONS.items():
        is_on = key in perms
        is_locked = key not in allowed
        if is_locked:
            icon = "🔒"
            cb = f"ba_locked|{key}"
        else:
            icon = "✔" if is_on else "✘"
            cb = f"ba|{actor_id}|{target_id}|{key}|{int(is_on)}"
        rows.append([InlineKeyboardButton(f"{icon} {label}", callback_data=cb)])

    rows.append([
        InlineKeyboardButton("✔ ارفعه دلوقتي", callback_data=f"ba_confirm|{actor_id}|{target_id}"),
        InlineKeyboardButton("✘ الغاء",        callback_data=f"ba_cancel|{actor_id}"),
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
                # ba|actor|target|key|is_on
                if len(p) >= 5 and bool(int(p[4])):
                    perms.add(p[3])
    return perms


# ════════════════════════════════════════════════════
# رفع مدير
# ════════════════════════════════════════════════════
@Client.on_message(
    (command(["botadmin"]) | command2(["رفع مدير", "رفع_مدير"])) & other_filters
)
async def promote_manager(c: Client, m: Message):
    try:
        await m.delete()
    except Exception:
        pass
    chat_id = m.chat.id

    if not m.from_user:
        return
    actor_id = m.from_user.id

    if not await can_manage_managers(c, chat_id, actor_id):
        return await m.reply(
            "✘ **رفع مدير ممنوع**\n\n"
            "هذا الأمر مخصص فقط لـ:\n"
            "• المالك الرسمي\n"
            "• أصحاب البوت\n"
            "• المديرين الذين يملكون صلاحية «رفع مديرين»"
        )

    target = None
    if m.reply_to_message and m.reply_to_message.from_user:
        target = m.reply_to_message.from_user
    elif len(m.command) >= 2:
        arg = m.command[1]
        try:
            target = await c.get_users(int(arg) if arg.lstrip("-").isdigit() else arg)
        except Exception:
            return await m.reply("✘ مش لاقي المستخدم ده")

    if not target:
        return await m.reply("رد على المستخدم أو اكتب معرفه/آيديه")
    if target.is_bot:
        return await m.reply("✘ مينفعش نرفع بوتات")
    if is_master(target.id):
        return await m.reply("👑 الواد ده فوق الكل أصلاً")

    # الصلاحيات الحالية إن وجدت، وإلا فاضية (المالك يحدد)
    current_perms = get_permissions(chat_id, target.id)
    keyboard = _perms_to_keyboard(actor_id, target.id, chat_id, current_perms)

    await m.reply(
        f"👤 **رفع مدير**\n\n"
        f"**المستخدم:** [{target.first_name}](tg://user?id={target.id})\n"
        f"**الآيدي:** `{target.id}`\n\n"
        f"اختار صلاحيات المدير داخل البوت ثم اضغط «ارفعه دلوقتي»:",
        reply_markup=keyboard
    )


# ════════════════════════════════════════════════════
# تنزيل مدير
# ════════════════════════════════════════════════════
@Client.on_message(
    (command(["rmbotadmin"]) | command2(["تنزيل مدير", "تنزل مدير", "شيل مدير"])) & other_filters
)
async def demote_manager(c: Client, m: Message):
    try:
        await m.delete()
    except Exception:
        pass
    chat_id = m.chat.id

    if not m.from_user:
        return
    if not await can_manage_managers(c, chat_id, m.from_user.id):
        return await m.reply("✘ تنزيل مدير ممنوع — للمالك / أصحاب البوت / مدير عنده صلاحية رفع مديرين فقط")

    target = None
    if m.reply_to_message and m.reply_to_message.from_user:
        target = m.reply_to_message.from_user
    elif len(m.command) >= 2:
        arg = m.command[1]
        try:
            target = await c.get_users(int(arg) if arg.lstrip("-").isdigit() else arg)
        except Exception:
            return await m.reply("✘ مش لاقي المستخدم ده")

    if not target:
        return await m.reply("رد على المستخدم أو اكتب معرفه")
    if not is_bot_admin(chat_id, target.id):
        return await m.reply("✘ الشخص ده مش مدير")

    remove_bot_admin(chat_id, target.id)
    await m.reply(f"✔ تم شيل [{target.first_name}](tg://user?id={target.id}) من المديرين")


# ════════════════════════════════════════════════════
# قائمة المديرين
# ════════════════════════════════════════════════════
@Client.on_message(
    (command(["botadmins"]) | command2(["قائمة المديرين", "قايمة المديرين", "المديرين"])) & other_filters
)
async def list_managers(c: Client, m: Message):
    try:
        await m.delete()
    except Exception:
        pass
    admins = get_bot_admins(m.chat.id)
    if not admins:
        return await m.reply("✘ مفيش مديرين في الجروب ده")

    text = "**⚙️ المديرين:**\n\n"
    for user_id, perms in admins.items():
        try:
            user = await c.get_users(user_id)
            name = user.first_name
        except Exception:
            name = str(user_id)
        perms_text = ", ".join(ALL_PERMISSIONS.get(p, p) for p in perms) or "بدون صلاحيات"
        text += f"👤 [{name}](tg://user?id={user_id})\n» {perms_text}\n\n"

    await m.reply(text, disable_web_page_preview=True)


# ════════════════════════════════════════════════════
# Callbacks
# ════════════════════════════════════════════════════
def _parse_actor(query: CallbackQuery):
    """يستخرج actor_id من الـ callback_data (موجود في كل أزرار ba)."""
    parts = query.data.split("|")
    # patterns:
    #  ba|actor|target|key|onoff
    #  ba_all|actor|target|onoff
    #  ba_confirm|actor|target
    #  ba_cancel|actor
    try:
        return int(parts[1])
    except Exception:
        return None


@Client.on_callback_query(filters.regex(r"^ba_locked\|"))
async def locked_perm(c: Client, query: CallbackQuery):
    await query.answer(
        "🔒 هذه الصلاحية لا يستطيع منحها سوى المالك / أصحاب البوت",
        show_alert=True
    )


@Client.on_callback_query(filters.regex(r"^ba\|"))
async def toggle_perm(c: Client, query: CallbackQuery):
    actor_id = _parse_actor(query)
    chat_id = query.message.chat.id

    if query.from_user.id != actor_id and not is_master(query.from_user.id):
        return await query.answer("✘ مش انت اللي بدأت العملية", show_alert=True)
    if not await can_manage_managers(c, chat_id, query.from_user.id):
        return await query.answer("✘ مش مسموح ليك", show_alert=True)

    parts = query.data.split("|")
    target_id = int(parts[2])
    key = parts[3]
    current = bool(int(parts[4]))

    # امنع منح صلاحية محظورة لو الـ actor مش master
    allowed = _allowed_perms_for(query.from_user.id, chat_id)
    if key not in allowed:
        return await query.answer("🔒 الصلاحية دي للمالك بس", show_alert=True)

    perms = _extract_perms(query.message.reply_markup)
    if current:
        perms.discard(key)
    else:
        perms.add(key)

    await query.message.edit_reply_markup(
        _perms_to_keyboard(actor_id, target_id, chat_id, perms)
    )
    await query.answer()


@Client.on_callback_query(filters.regex(r"^ba_all\|"))
async def toggle_all(c: Client, query: CallbackQuery):
    actor_id = _parse_actor(query)
    chat_id = query.message.chat.id

    if query.from_user.id != actor_id and not is_master(query.from_user.id):
        return await query.answer("✘ مش انت اللي بدأت العملية", show_alert=True)
    if not await can_manage_managers(c, chat_id, query.from_user.id):
        return await query.answer("✘ مش مسموح ليك", show_alert=True)

    parts = query.data.split("|")
    target_id = int(parts[2])
    turn_on = bool(int(parts[3]))

    allowed = _allowed_perms_for(query.from_user.id, chat_id)
    if turn_on:
        new_perms = set(allowed)  # كل المسموح بس
    else:
        new_perms = set()

    await query.message.edit_reply_markup(
        _perms_to_keyboard(actor_id, target_id, chat_id, new_perms)
    )
    await query.answer("تم")


@Client.on_callback_query(filters.regex(r"^ba_confirm\|"))
async def confirm_manager(c: Client, query: CallbackQuery):
    actor_id = _parse_actor(query)
    chat_id = query.message.chat.id

    if query.from_user.id != actor_id and not is_master(query.from_user.id):
        return await query.answer("✘ مش انت اللي بدأت العملية", show_alert=True)
    if not await can_manage_managers(c, chat_id, query.from_user.id):
        return await query.answer("✘ مش مسموح ليك", show_alert=True)

    parts = query.data.split("|")
    target_id = int(parts[2])

    perms = _extract_perms(query.message.reply_markup)

    # تأمين: شيل أي صلاحية محظورة لو الـ actor مش master
    allowed = _allowed_perms_for(query.from_user.id, chat_id)
    perms = perms & allowed

    add_bot_admin(chat_id, target_id, perms)
    target = await c.get_users(target_id)

    if perms:
        perms_text = "\n".join(
            f"  ✔ {ALL_PERMISSIONS.get(k, k)}" for k in perms
        )
    else:
        perms_text = "  (بدون أي صلاحيات)"

    await query.message.edit_text(
        f"✔ **تم رفع المدير بنجاح**\n\n"
        f"👤 **المستخدم:** [{target.first_name}](tg://user?id={target_id})\n"
        f"🏠 **المجموعة:** `{chat_id}`\n\n"
        f"**الصلاحيات الممنوحة:**\n{perms_text}"
    )
    await query.answer()


@Client.on_callback_query(filters.regex(r"^ba_cancel\|"))
async def cancel_manager(c: Client, query: CallbackQuery):
    actor_id = _parse_actor(query)
    if query.from_user.id != actor_id and not is_master(query.from_user.id):
        return await query.answer("✘ مش انت اللي بدأت العملية", show_alert=True)
    try:
        await query.message.delete()
    except Exception:
        pass
    await query.answer()
