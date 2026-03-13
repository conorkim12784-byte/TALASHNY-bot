# promote.py — رفع مشرف مع أزرار صلاحيات + مراقبة حظر تلقائي

from collections import defaultdict

from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, ChatPrivileges
)
from pyrogram.errors import ChatAdminRequired

from driver.filters import command, command2, other_filters
from driver.decorators import authorized_users_only

# ═══════════════════════════════════════
# عداد الحظر: { chat_id: { admin_id: count } }
# ═══════════════════════════════════════
ban_counter: dict = defaultdict(lambda: defaultdict(int))

# الحد الافتراضي لكل الجروبات
DEFAULT_BAN_LIMIT = 20
# حد مخصص لكل جروب: { chat_id: limit }
ban_limits: dict = defaultdict(lambda: DEFAULT_BAN_LIMIT)

# الآيدي المسموح له بتغيير الحد بالإضافة لمالك الجروب
SUPER_USER_ID = 1923931101


def BAN_LIMIT(chat_id: int) -> int:
    return ban_limits[chat_id]



# ═══════════════════════════════════════
# أمر تغيير حد الحظر
# ═══════════════════════════════════════
@Client.on_message((command(["setbanlimit"]) | command2(["حد_الحظر"])) & other_filters)
async def set_ban_limit(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    user_id = m.from_user.id

    is_super = (user_id == SUPER_USER_ID)
    is_owner = False
    try:
        member = await c.get_chat_member(chat_id, user_id)
        is_owner = (member.status.value == "creator")
    except Exception:
        pass

    if not is_super and not is_owner:
        return await m.reply("❌ **هذا الأمر لمالك المجموعة فقط**")

    if len(m.command) < 2 or not m.command[1].isdigit():
        current = ban_limits[chat_id]
        return await m.reply(
            f"**الاستخدام:** `/حد_الحظر [رقم]`\n\n"
            f"**الحد الحالي:** `{current}` حظر\n"
            f"**مثال:** `/حد_الحظر 10`"
        )

    new_limit = int(m.command[1])
    if new_limit < 1:
        return await m.reply("❌ **الحد يجب أن يكون أكبر من 0**")

    old_limit = ban_limits[chat_id]
    ban_limits[chat_id] = new_limit

    await m.reply(
        f"✅ **تم تغيير حد الحظر**\n\n"
        f"📊 **الحد القديم:** `{old_limit}`\n"
        f"📊 **الحد الجديد:** `{new_limit}`\n\n"
        f"أي مشرف يتجاوز **{new_limit}** حظر سيُنزَل تلقائياً."
    )


# ═══════════════════════════════════════
# بناء أزرار الصلاحيات
# ═══════════════════════════════════════
def build_permissions_keyboard(user_id: int, title: str, perms: dict) -> InlineKeyboardMarkup:
    def btn(label, key):
        icon = "✅" if perms.get(key) else "❌"
        return InlineKeyboardButton(
            f"{icon} {label}",
            callback_data=f"prm|{user_id}|{key}|{int(perms.get(key, False))}"
        )

    return InlineKeyboardMarkup([
        [btn("تغيير معلومات المجموعة", "change_info"),
         btn("حذف الرسائل", "delete_messages")],
        [btn("حظر الأعضاء", "ban_users"),
         btn("دعوة أعضاء", "invite_users")],
        [btn("تثبيت الرسائل", "pin_messages"),
         btn("إدارة المكالمات", "manage_video_chats")],
        [btn("إضافة مشرفين", "add_admins"),
         btn("مجهول الهوية", "is_anonymous")],
        [InlineKeyboardButton(
            f"✏️ اللقب: {title or 'بدون لقب'}",
            callback_data=f"prm_title|{user_id}"
        )],
        [
            InlineKeyboardButton("✅ رفع الآن", callback_data=f"prm_confirm|{user_id}|{title}"),
            InlineKeyboardButton("❌ إلغاء", callback_data="prm_cancel"),
        ],
    ])


# ═══════════════════════════════════════
# أمر رفع مشرف
# ═══════════════════════════════════════
@Client.on_message((command(["promote"]) | command2(["رفع"])) & other_filters)
@authorized_users_only
async def promote_user(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    target = None
    title = ""

    if m.reply_to_message:
        target = m.reply_to_message.from_user
        parts = m.text.split(None, 1)
        title = parts[1].strip() if len(parts) > 1 else ""
    elif len(m.command) >= 2:
        arg = m.command[1]
        parts = m.text.split(None, 2)
        title = parts[2].strip() if len(parts) > 2 else ""
        try:
            target = await c.get_users(int(arg) if arg.lstrip("-").isdigit() else arg)
        except Exception:
            return await m.reply("❌ **لم يتم العثور على المستخدم**")
    else:
        return await m.reply(
            "**الاستخدام:**\n"
            "» رد على مستخدم: `/رفع محمد`\n"
            "» بالمعرف: `/رفع @username محمد`\n"
            "» بالآيدي: `/رفع 123456789 محمد`"
        )

    if not target:
        return await m.reply("❌ **لم يتم التعرف على المستخدم**")
    if target.is_bot:
        return await m.reply("❌ **لا يمكن رفع البوتات**")

    perms = {
        "change_info": True, "delete_messages": True,
        "ban_users": True, "invite_users": True,
        "pin_messages": True, "manage_video_chats": True,
        "add_admins": False, "is_anonymous": False,
    }

    await m.reply(
        f"👤 **رفع مشرف**\n\n"
        f"**المستخدم:** [{target.first_name}](tg://user?id={target.id})\n"
        f"**اللقب:** `{title or 'بدون لقب'}`\n\n"
        f"حدد الصلاحيات ثم اضغط **رفع الآن**:",
        reply_markup=build_permissions_keyboard(target.id, title, perms)
    )


# ═══════════════════════════════════════
# callback — تبديل صلاحية
# ═══════════════════════════════════════
@Client.on_callback_query(filters.regex(r"^prm\|"))
async def toggle_permission(c: Client, query: CallbackQuery):
    member = await c.get_chat_member(query.message.chat.id, query.from_user.id)
    if member.status.value not in ("administrator", "creator"):
        return await query.answer("❌ فقط المشرفون يمكنهم التعديل", show_alert=True)

    _, user_id, key, current = query.data.split("|")
    user_id = int(user_id)

    perms = {}
    title = ""
    for row in query.message.reply_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data and btn.callback_data.startswith("prm|"):
                p = btn.callback_data.split("|")
                perms[p[2]] = bool(int(p[3]))
            elif btn.callback_data and btn.callback_data.startswith("prm_confirm|"):
                conf = btn.callback_data.split("|", 2)
                title = conf[2] if len(conf) > 2 else ""

    perms[key] = not bool(int(current))
    await query.edit_message_reply_markup(build_permissions_keyboard(user_id, title, perms))
    await query.answer("✅ تم التعديل")


# ═══════════════════════════════════════
# callback — تأكيد الرفع
# ═══════════════════════════════════════
@Client.on_callback_query(filters.regex(r"^prm_confirm\|"))
async def confirm_promote(c: Client, query: CallbackQuery):
    member = await c.get_chat_member(query.message.chat.id, query.from_user.id)
    if member.status.value not in ("administrator", "creator"):
        return await query.answer("❌ فقط المشرفون يمكنهم الرفع", show_alert=True)

    parts = query.data.split("|", 2)
    user_id = int(parts[1])
    title = parts[2] if len(parts) > 2 else ""

    perms = {}
    for row in query.message.reply_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data and btn.callback_data.startswith("prm|"):
                p = btn.callback_data.split("|")
                perms[p[2]] = bool(int(p[3]))

    PERM_NAMES = {
        "change_info": "تغيير معلومات المجموعة",
        "delete_messages": "حذف الرسائل",
        "ban_users": "حظر الأعضاء",
        "invite_users": "دعوة أعضاء",
        "pin_messages": "تثبيت الرسائل",
        "manage_video_chats": "إدارة المكالمات",
        "add_admins": "إضافة مشرفين",
        "is_anonymous": "مجهول الهوية",
    }

    try:
        await c.promote_chat_member(
            query.message.chat.id, user_id,
            privileges=ChatPrivileges(
                can_change_info=perms.get("change_info", False),
                can_delete_messages=perms.get("delete_messages", False),
                can_restrict_members=perms.get("ban_users", False),
                can_invite_users=perms.get("invite_users", False),
                can_pin_messages=perms.get("pin_messages", False),
                can_manage_video_chats=perms.get("manage_video_chats", False),
                can_promote_members=perms.get("add_admins", False),
                is_anonymous=perms.get("is_anonymous", False),
            )
        )
        if title:
            try:
                await c.set_administrator_title(query.message.chat.id, user_id, title)
            except Exception:
                pass

        target = await c.get_users(user_id)
        perms_text = "\n".join(
            f"  {'✅' if v else '❌'} {PERM_NAMES.get(k, k)}"
            for k, v in perms.items()
        )
        await query.edit_message_text(
            f"✅ **تم رفع المشرف بنجاح**\n\n"
            f"👤 **المشرف:** [{target.first_name}](tg://user?id={user_id})\n"
            f"✏️ **اللقب:** `{title or 'بدون لقب'}`\n\n"
            f"**الصلاحيات:**\n{perms_text}"
        )
    except ChatAdminRequired:
        await query.answer("❌ البوت ليس لديه صلاحية رفع مشرفين", show_alert=True)
    except Exception as e:
        await query.answer(f"❌ خطأ: {e}", show_alert=True)


# ═══════════════════════════════════════
# callback — إلغاء
# ═══════════════════════════════════════
@Client.on_callback_query(filters.regex("^prm_cancel$"))
async def cancel_promote(c: Client, query: CallbackQuery):
    await query.edit_message_text("❌ **تم إلغاء العملية**")


# ═══════════════════════════════════════
# مراقبة تغييرات الأعضاء تلقائياً
# ═══════════════════════════════════════
@Client.on_chat_member_updated(filters.group)
async def watch_member_changes(c: Client, update):
    try:
        old = update.old_chat_member
        new = update.new_chat_member
        if not old or not new:
            return

        old_status = old.status.value if old.status else ""
        new_status = new.status.value if new.status else ""
        chat_id = update.chat.id
        user = new.user

        # ── عضو اتحظر يدوياً ──
        if new_status == "banned" and update.from_user:
            admin_id = update.from_user.id

            # متراقبش لو البوت نفسه حظر
            me = await c.get_me()
            if admin_id == me.id:
                return

            # تأكد إن اللي حظر مشرف فعلاً
            try:
                adm = await c.get_chat_member(chat_id, admin_id)
                if adm.status.value not in ("administrator", "creator"):
                    return
            except Exception:
                return

            ban_counter[chat_id][admin_id] += 1
            count = ban_counter[chat_id][admin_id]

            await c.send_message(
                chat_id,
                f"🚫 **إشعار حظر**\n\n"
                f"👤 **المحظور:** [{user.first_name}](tg://user?id={user.id})\n"
                f"👮 **بواسطة:** [{update.from_user.first_name}](tg://user?id={admin_id})\n"
                f"📊 **عداد الحظر:** `{count}/{BAN_LIMIT(chat_id)}`"
            )

            if count >= BAN_LIMIT(chat_id):
                await _auto_demote(c, chat_id, admin_id, count, BAN_LIMIT(chat_id))

        # ── مشرف اتنزّل ──
        elif old_status == "administrator" and new_status not in ("administrator", "creator"):
            who = ""
            if update.from_user:
                who = f"\n👮 **بواسطة:** [{update.from_user.first_name}](tg://user?id={update.from_user.id})"
            await c.send_message(
                chat_id,
                f"📢 **إشعار: نزول مشرف**\n\n"
                f"👤 **المشرف:** [{user.first_name}](tg://user?id={user.id}){who}"
            )

        # ── عضو اترفّع مشرف ──
        elif old_status not in ("administrator", "creator") and new_status == "administrator":
            who = ""
            if update.from_user:
                who = f"\n👮 **بواسطة:** [{update.from_user.first_name}](tg://user?id={update.from_user.id})"
            await c.send_message(
                chat_id,
                f"📢 **إشعار: رفع مشرف جديد**\n\n"
                f"👤 **المشرف الجديد:** [{user.first_name}](tg://user?id={user.id}){who}"
            )

    except Exception:
        pass


async def _auto_demote(c: Client, chat_id: int, admin_id: int, count: int, limit: int):
    try:
        admin = await c.get_users(admin_id)
        await c.promote_chat_member(
            chat_id, admin_id,
            privileges=ChatPrivileges(
                can_change_info=False, can_delete_messages=False,
                can_restrict_members=False, can_invite_users=False,
                can_pin_messages=False, can_manage_video_chats=False,
                can_promote_members=False, is_anonymous=False,
            )
        )
        ban_counter[chat_id][admin_id] = 0
        await c.send_message(
            chat_id,
            f"⚠️ **تنبيه تلقائي**\n\n"
            f"👮 **المشرف:** [{admin.first_name}](tg://user?id={admin_id})\n"
            f"🚫 **قام بحظر {count} مستخدم يدوياً**\n\n"
            f"✅ **تم نزوله من الإشراف تلقائياً** بسبب تجاوز الحد `{limit}` حظر."
        )
    except Exception as e:
        await c.send_message(
            chat_id,
            f"⚠️ المشرف [{admin_id}](tg://user?id={admin_id}) تجاوز {BAN_LIMIT} حظر "
            f"لكن فشل النزول التلقائي: `{e}`"
        )
