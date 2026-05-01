# promote.py — رفع مشرف + مراقبة حظر تلقائي + عزل من يتخطى الحد
#
# تحديثات هذه النسخة:
#   • أمر "رفع مشرف" — لو ما اتكتبش لقب يستخدم لقب افتراضي "مشرف".
#   • تمت إضافة كل صلاحيات تيليجرام الجديدة:
#       - can_manage_topics (إدارة المواضيع — للسوبر جروبات اللي مفعلة Topics)
#       - can_post_stories  (نشر القصص)
#       - can_edit_stories  (تعديل القصص)
#       - can_delete_stories(حذف القصص)
#   • نفس قواعد منع التخطي ومراقبة الحظر التلقائي.

from collections import defaultdict

from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, ChatPrivileges
)
from pyrogram.errors import ChatAdminRequired

from driver.filters import command, command2, other_filters
from driver.permissions import get_rank, can_target
from config import SUDO_USERS

# ═══════════════════════════════════════
# إعدادات
# ═══════════════════════════════════════
ban_counter: dict = defaultdict(lambda: defaultdict(int))
DEFAULT_BAN_LIMIT = 20
ban_limits: dict = defaultdict(lambda: DEFAULT_BAN_LIMIT)
SUPER_USER_ID = 1923931101

DEFAULT_TITLE = "مشرف"  # اللقب الافتراضي لو ما اتكتبش لقب


def get_ban_limit(chat_id: int) -> int:
    return ban_limits[chat_id]


def _status_str(status) -> str:
    if status is None:
        return ""
    return getattr(status, "value", str(status)).lower()


# ═══════════════════════════════════════
# التحقق من الصلاحية — مالك الجروب أو السوبر يوزر فقط
# ═══════════════════════════════════════
async def is_allowed(c: Client, chat_id: int, user_id: int) -> bool:
    if user_id is None:
        return False
    if user_id in SUDO_USERS or user_id == SUPER_USER_ID:
        return True
    try:
        member = await c.get_chat_member(chat_id, user_id)
        return _status_str(member.status) in ("creator", "owner", "administrator")
    except Exception:
        return False


# ═══════════════════════════════════════
# أسماء الصلاحيات (للعرض)
# ═══════════════════════════════════════
PERM_NAMES = {
    "change_info":       "تغيير معلومات المجموعة",
    "delete_messages":   "حذف الرسائل",
    "ban_users":         "حظر الأعضاء وإلغاء حظرهم",
    "invite_users":      "دعوة المستخدمين عبر الروابط",
    "pin_messages":      "تثبيت الرسائل",
    "manage_video_chats":"إدارة مكالمات الفيديو",
    "is_anonymous":      "البقاء مجهول الهوية",
    "add_admins":        "إضافة مشرفين جدد",
    # ── الجديدة ──
    "manage_topics":     "إدارة المواضيع (Topics)",
    "post_stories":      "نشر القصص",
    "edit_stories":      "تعديل القصص",
    "delete_stories":    "حذف القصص",
}


# ═══════════════════════════════════════
# بناء أزرار الصلاحيات
# ═══════════════════════════════════════
def build_keyboard(user_id: int, perms: dict) -> InlineKeyboardMarkup:
    def btn(label, key):
        icon = "✔" if perms.get(key) else "✘"
        val = int(perms.get(key, False))
        return InlineKeyboardButton(
            f"{icon} {label}",
            callback_data=f"prm|{user_id}|{key}|{val}"
        )

    return InlineKeyboardMarkup([
        [btn("تغيير معلومات المجموعة", "change_info")],
        [btn("حذف الرسائل", "delete_messages")],
        [btn("حظر الأعضاء وإلغاء حظرهم", "ban_users")],
        [btn("دعوة المستخدمين عبر الروابط", "invite_users")],
        [btn("تثبيت الرسائل", "pin_messages")],
        [btn("إدارة مكالمات الفيديو", "manage_video_chats")],
        [btn("إدارة المواضيع (Topics)", "manage_topics")],
        [btn("نشر القصص", "post_stories")],
        [btn("تعديل القصص", "edit_stories")],
        [btn("حذف القصص", "delete_stories")],
        [btn("البقاء مجهول الهوية", "is_anonymous")],
        [btn("إضافة مشرفين جدد", "add_admins")],
        [
            InlineKeyboardButton("✔ رفع الآن", callback_data=f"prm_confirm|{user_id}"),
            InlineKeyboardButton("✘ إلغاء", callback_data="prm_cancel"),
        ],
    ])


pending_titles: dict = {}


# ═══════════════════════════════════════
# أمر رفع مشرف
# الصيغة: "رفع مشرف <لقب>"
# لو ما اتكتبش لقب → يُستخدم "مشرف" كلقب افتراضي.
# ═══════════════════════════════════════
@Client.on_message(
    (command(["promote"]) | command2(["رفع مشرف", "رفع_مشرف"])) & other_filters
)
async def promote_user(c: Client, m: Message):
    try:
        await m.delete()
    except Exception:
        pass
    chat_id = m.chat.id

    if not m.from_user:
        return
    user_id = m.from_user.id

    if not await is_allowed(c, chat_id, user_id):
        return await m.reply("✘ **هذا الأمر لمالك المجموعة فقط**")

    target = None
    title = ""

    # حدد الكلمات اللي تخص الأمر نفسه عشان نفصلها عن اللقب
    raw = (m.text or "").strip()
    # نشيل أول كلمتين (رفع + مشرف) أو الكلمة الواحدة (رفع_مشرف / /promote)
    lowered = raw.lower()
    title_part = ""
    if m.reply_to_message and m.reply_to_message.from_user:
        target = m.reply_to_message.from_user
        # كل اللي بعد "رفع مشرف" يبقى لقب
        for prefix in ("رفع مشرف", "رفع_مشرف", "/promote", "promote"):
            if lowered.startswith(prefix):
                title_part = raw[len(prefix):].strip()
                break
        title = title_part
    elif len(m.command) >= 2:
        arg = m.command[1]
        try:
            target = await c.get_users(int(arg) if arg.lstrip("-").isdigit() else arg)
        except Exception:
            return await m.reply("✘ **لم يتم العثور على المستخدم**")
        # اللقب = كل اللي بعد المعرف
        parts = m.text.split(None, 2)
        title = parts[2].strip() if len(parts) > 2 else ""
    else:
        return await m.reply(
            "**الاستخدام:**\n"
            "» رد على المستخدم: `رفع مشرف اللقب`\n"
            "» بالمعرف: `رفع مشرف @username اللقب`\n"
            "» بالآيدي: `رفع مشرف 123456789 اللقب`\n\n"
            f"_اللقب اختياري — لو ما اتكتبش يبقى الافتراضي `{DEFAULT_TITLE}`_"
        )

    if not target:
        return await m.reply("✘ **لم يتم التعرف على المستخدم**")
    if target.is_bot:
        return await m.reply("✘ **لا يمكن رفع البوتات**")

    # لقب افتراضي
    if not title:
        title = DEFAULT_TITLE

    # منع تخطي الرتب
    actor_rank = await get_rank(c, chat_id, user_id)
    target_rank = await get_rank(c, chat_id, target.id)
    if not can_target(actor_rank, target_rank):
        return await m.reply("❌ لا يمكنك رفع شخص رتبته أعلى أو مساوية لك")

    perms = {
        "change_info": True,
        "delete_messages": True,
        "ban_users": True,
        "invite_users": True,
        "pin_messages": True,
        "manage_video_chats": True,
        # الجديدة — افتراضي مفعل بشكل آمن
        "manage_topics": True,
        "post_stories": False,
        "edit_stories": False,
        "delete_stories": False,
        "is_anonymous": False,
        "add_admins": False,
    }

    await m.reply(
        f"👤 **رفع مشرف**\n\n"
        f"**المستخدم:** [{target.first_name}](tg://user?id={target.id})\n"
        f"**الآيدي:** `{target.id}`\n"
        f"**اللقب:** `{title}`\n\n"
        f"اختر صلاحيات الجروب:",
        reply_markup=build_keyboard(target.id, perms)
    )

    pending_titles[target.id] = title


@Client.on_callback_query(filters.regex(r"^prm\|"))
async def toggle_permission(c: Client, query: CallbackQuery):
    if not await is_allowed(c, query.message.chat.id, query.from_user.id):
        return await query.answer("✘ فقط مالك المجموعة", show_alert=True)

    _, user_id, key, current = query.data.split("|")
    user_id = int(user_id)

    perms = {}
    for row in query.message.reply_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data and btn.callback_data.startswith("prm|"):
                p = btn.callback_data.split("|")
                perms[p[2]] = bool(int(p[3]))

    perms[key] = not bool(int(current))
    await query.edit_message_reply_markup(build_keyboard(user_id, perms))
    await query.answer()


@Client.on_callback_query(filters.regex(r"^prm_confirm\|"))
async def confirm_promote(c: Client, query: CallbackQuery):
    if not await is_allowed(c, query.message.chat.id, query.from_user.id):
        return await query.answer("✘ فقط مالك المجموعة", show_alert=True)

    user_id = int(query.data.split("|")[1])
    title = pending_titles.pop(user_id, "") or DEFAULT_TITLE

    perms = {}
    for row in query.message.reply_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data and btn.callback_data.startswith("prm|"):
                p = btn.callback_data.split("|")
                perms[p[2]] = bool(int(p[3]))

    # نبني ChatPrivileges مع دعم آمن للصلاحيات الجديدة
    privileges_kwargs = dict(
        can_change_info=perms.get("change_info", False),
        can_delete_messages=perms.get("delete_messages", False),
        can_restrict_members=perms.get("ban_users", False),
        can_invite_users=perms.get("invite_users", False),
        can_pin_messages=perms.get("pin_messages", False),
        can_manage_video_chats=perms.get("manage_video_chats", False),
        is_anonymous=perms.get("is_anonymous", False),
        can_promote_members=perms.get("add_admins", False),
    )

    # محاولة دعم الصلاحيات الجديدة (لو الـ pyrogram المركّب يدعمها)
    optional = {
        "can_manage_topics":  perms.get("manage_topics", False),
        "can_post_stories":   perms.get("post_stories", False),
        "can_edit_stories":   perms.get("edit_stories", False),
        "can_delete_stories": perms.get("delete_stories", False),
    }
    for k, v in optional.items():
        try:
            ChatPrivileges(**{k: v})  # probe
            privileges_kwargs[k] = v
        except TypeError:
            # نسخة pyrogram دي ما تدعمش الصلاحية ده — تجاهل بهدوء
            pass

    try:
        await c.promote_chat_member(
            query.message.chat.id, user_id,
            privileges=ChatPrivileges(**privileges_kwargs)
        )
        try:
            await c.set_administrator_title(query.message.chat.id, user_id, title)
        except Exception:
            pass

        target = await c.get_users(user_id)
        perms_text = "\n".join(
            f"  {'✔' if v else '✘'} {PERM_NAMES.get(k, k)}"
            for k, v in perms.items()
        )
        await query.edit_message_text(
            f"✔ **تم رفع المشرف بنجاح**\n\n"
            f"👤 **المشرف:** [{target.first_name}](tg://user?id={user_id})\n"
            f"✏️ **اللقب:** `{title}`\n\n"
            f"**الصلاحيات:**\n{perms_text}"
        )
    except ChatAdminRequired:
        await query.answer("✘ البوت ليس لديه صلاحية رفع مشرفين", show_alert=True)
    except Exception as e:
        await query.answer(f"✘ خطأ: {e}", show_alert=True)


@Client.on_callback_query(filters.regex("^prm_cancel$"))
async def cancel_promote(c: Client, query: CallbackQuery):
    await query.edit_message_text("✘ **تم إلغاء العملية**")


# ═══════════════════════════════════════
# أمر تغيير حد الحظر
# ═══════════════════════════════════════
@Client.on_message((command(["setbanlimit"]) | command2(["حد الحظر", "حد_الحظر"])) & other_filters)
async def set_ban_limit(c: Client, m: Message):
    try:
        await m.delete()
    except Exception:
        pass
    chat_id = m.chat.id

    if not m.from_user or not await is_allowed(c, chat_id, m.from_user.id):
        return await m.reply("✘ **هذا الأمر لمالك المجموعة فقط**")

    if len(m.command) < 2 or not m.command[1].isdigit():
        return await m.reply(
            f"**الاستخدام:** `حد الحظر [رقم]`\n\n"
            f"**الحد الحالي:** `{get_ban_limit(chat_id)}` حظر\n"
            f"**مثال:** `حد الحظر 10`"
        )

    new_limit = int(m.command[1])
    if new_limit < 1:
        return await m.reply("✘ **الحد يجب أن يكون أكبر من 0**")

    old_limit = get_ban_limit(chat_id)
    ban_limits[chat_id] = new_limit

    await m.reply(
        f"✔ **تم تغيير حد الحظر**\n\n"
        f"📊 **الحد القديم:** `{old_limit}`\n"
        f"📊 **الحد الجديد:** `{new_limit}`\n\n"
        f"أي مشرف يتجاوز **{new_limit}** حظر يدوياً سيُنزَل تلقائياً."
    )


# ═══════════════════════════════════════
# مراقبة تغييرات الأعضاء + عزل المتخطي للحد
# ═══════════════════════════════════════
@Client.on_chat_member_updated(filters.group, group=-1)
async def watch_member_changes(c: Client, update):
    try:
        old = update.old_chat_member
        new = update.new_chat_member
        if not old or not new:
            return

        old_status = _status_str(old.status)
        new_status = _status_str(new.status)
        chat_id = update.chat.id
        target_user = new.user or old.user
        if not target_user:
            return

        actor = update.from_user

        if new_status in ("banned", "kicked") and old_status not in ("banned", "kicked") and actor:
            admin_id = actor.id
            try:
                me = await c.get_me()
            except Exception:
                me = None
            if me and admin_id == me.id:
                return

            try:
                adm = await c.get_chat_member(chat_id, admin_id)
                adm_status = _status_str(adm.status)
            except Exception:
                return
            if adm_status not in ("administrator",):
                return

            ban_counter[chat_id][admin_id] += 1
            count = ban_counter[chat_id][admin_id]
            limit = get_ban_limit(chat_id)

            try:
                await c.send_message(
                    chat_id,
                    f"🚫 **إشعار حظر**\n\n"
                    f"👤 **المحظور:** [{target_user.first_name}](tg://user?id={target_user.id})\n"
                    f"👮 **بواسطة:** [{actor.first_name}](tg://user?id={admin_id})\n"
                    f"📊 **عداد الحظر:** `{count}/{limit}`"
                )
            except Exception:
                pass

            if count >= limit:
                await _auto_demote(c, chat_id, admin_id, count, limit)
            return

        if old_status == "administrator" and new_status not in ("administrator", "creator", "owner"):
            who = ""
            if actor:
                who = f"\n👮 **بواسطة:** [{actor.first_name}](tg://user?id={actor.id})"
            try:
                await c.send_message(
                    chat_id,
                    f"📢 **إشعار: نزول مشرف**\n\n"
                    f"👤 **المشرف:** [{target_user.first_name}](tg://user?id={target_user.id}){who}"
                )
            except Exception:
                pass
            return

        if old_status not in ("administrator", "creator", "owner") and new_status == "administrator":
            who = ""
            if actor:
                who = f"\n👮 **بواسطة:** [{actor.first_name}](tg://user?id={actor.id})"
            try:
                await c.send_message(
                    chat_id,
                    f"📢 **إشعار: رفع مشرف جديد**\n\n"
                    f"👤 **المشرف الجديد:** [{target_user.first_name}](tg://user?id={target_user.id}){who}"
                )
            except Exception:
                pass
            return

    except Exception as e:
        print(f"[watch_member_changes] {e}")


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
            f"🚫 **تجاوز {count} حظر يدوي**\n\n"
            f"✔ **تم نزوله من الإشراف تلقائياً** — الحد المسموح: `{limit}`"
        )
    except Exception as e:
        try:
            await c.send_message(
                chat_id,
                f"⚠️ المشرف [{admin_id}](tg://user?id={admin_id}) تجاوز الحد "
                f"لكن فشل النزول التلقائي: `{e}`"
            )
        except Exception:
            pass
