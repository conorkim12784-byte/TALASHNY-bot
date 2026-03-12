# ═══════════════════════════════════════
# 👑 نظام الرفع المتقدم
# ═══════════════════════════════════════

from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, ChatPrivileges
)
from pyrogram.enums import ChatMemberStatus
from driver.filters import command2, other_filters

DEV_IDS = [1923931101, 5340100457]

def is_dev(user_id):
    return user_id in DEV_IDS

async def is_owner_or_dev(client, chat_id, user_id):
    if is_dev(user_id):
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status == ChatMemberStatus.OWNER
    except:
        return False

PRIVILEGES_MAP = {
    "change":   ChatPrivileges(can_change_info=True),
    "delete":   ChatPrivileges(can_change_info=True, can_delete_messages=True),
    "restrict": ChatPrivileges(can_change_info=True, can_delete_messages=True, can_restrict_members=True),
    "invite":   ChatPrivileges(can_change_info=True, can_delete_messages=True, can_restrict_members=True, can_invite_users=True),
    "pin":      ChatPrivileges(can_change_info=True, can_delete_messages=True, can_restrict_members=True, can_invite_users=True, can_pin_messages=True),
    "video":    ChatPrivileges(can_change_info=True, can_delete_messages=True, can_restrict_members=True, can_invite_users=True, can_pin_messages=True, can_manage_video_chats=True),
    "promote":  ChatPrivileges(can_change_info=True, can_delete_messages=True, can_restrict_members=True, can_invite_users=True, can_pin_messages=True, can_manage_video_chats=True, can_promote_members=True),
}

PRIVILEGE_TEXT = {
    "change":   "تغيير معلومات المجموعة",
    "delete":   "حذف الرسائل",
    "restrict": "حظر المستخدمين",
    "invite":   "دعوة المستخدمين",
    "pin":      "تثبيت الرسائل",
    "video":    "إدارة البثوث المباشرة",
    "promote":  "كل الصلاحيات",
}


@Client.on_message(filters.group & command2(["رفع"]) & other_filters)
async def promote_cmd(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not await is_owner_or_dev(client, chat_id, user_id):
        return

    if len(message.command) < 2 or message.command[1] != "مشرف":
        return await message.reply(
            "**الاستخدام:**\n"
            "رد على المستخدم واكتب:\n"
            "`/رفع مشرف [لقب اختياري]`"
        )

    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("❌ **رد على المستخدم اللي تريد ترفعه**")

    target = message.reply_to_message.from_user
    title = " ".join(message.command[2:]) if len(message.command) > 2 else ""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ تغيير معلومات المجموعة",  callback_data=f"prm_change_{chat_id}_{target.id}_{user_id}")],
        [InlineKeyboardButton("2️⃣ حذف الرسائل",             callback_data=f"prm_delete_{chat_id}_{target.id}_{user_id}")],
        [InlineKeyboardButton("3️⃣ حظر المستخدمين",          callback_data=f"prm_restrict_{chat_id}_{target.id}_{user_id}")],
        [InlineKeyboardButton("4️⃣ دعوة المستخدمين",         callback_data=f"prm_invite_{chat_id}_{target.id}_{user_id}")],
        [InlineKeyboardButton("5️⃣ تثبيت الرسائل",           callback_data=f"prm_pin_{chat_id}_{target.id}_{user_id}")],
        [InlineKeyboardButton("6️⃣ إدارة البثوث المباشرة",   callback_data=f"prm_video_{chat_id}_{target.id}_{user_id}")],
        [InlineKeyboardButton("⭐ كل الصلاحيات",             callback_data=f"prm_promote_{chat_id}_{target.id}_{user_id}")],
        [InlineKeyboardButton("🗑 إلغاء",                    callback_data="prm_del")]
    ])

    await message.reply(
        f"👮 **رفع مشرف**\n\n"
        f"👤 **المستخدم:** {target.mention}\n"
        f"🏷️ **اللقب:** `{title if title else 'بدون لقب'}`\n\n"
        f"اختر الصلاحيات (متراكمة من 1 لـ 7):",
        reply_markup=keyboard
    )


@Client.on_callback_query(filters.regex(r"^prm_(\w+)_(\-?\d+)_(\d+)_(\d+)$"))
async def promote_callback(client: Client, query: CallbackQuery):
    parts = query.data.split("_")
    action    = parts[1]
    chat_id   = int(parts[2])
    target_id = int(parts[3])
    owner_id  = int(parts[4])

    if query.from_user.id != owner_id:
        return await query.answer("❌ هذا الأمر مش ليك!", show_alert=True)
    if action not in PRIVILEGES_MAP:
        return

    try:
        target = await client.get_users(target_id)
        await client.promote_chat_member(chat_id, target_id, privileges=PRIVILEGES_MAP[action])
        await query.message.edit_text(
            f"✅ **تم الرفع بنجاح**\n\n"
            f"👤 **المشرف:** {target.mention}\n"
            f"🔑 **الصلاحية:** `{PRIVILEGE_TEXT[action]}`"
        )
    except Exception as e:
        await query.message.edit_text(f"❌ **فشل الرفع:**\n`{e}`")


@Client.on_callback_query(filters.regex("^prm_del$"))
async def prm_delete(client: Client, query: CallbackQuery):
    await query.message.delete()
