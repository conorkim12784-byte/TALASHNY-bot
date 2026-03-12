# ═══════════════════════════════════════
# 🛡️ نظام الحماية والكتم والرتب والأوامر
# ═══════════════════════════════════════

import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, ChatPrivileges
)
from pyrogram.enums import ChatMemberStatus, ChatType
from config import SUDO_USERS
from driver.filters import command, command2, other_filters
from driver.queues import QUEUE

DEV_IDS = [1923931101, 5340100457]

# تخزين عدد الحظرات لكل مشرف
ban_count = {}       # {chat_id: {user_id: count}}
muted_users = {}     # {chat_id: {user_id: True}}
bot_managers = {}    # {chat_id: {user_id: True}}
song_requester = {}  # {chat_id: {"mention": ...}}

GIF_URL = "https://i.postimg.cc/wxV3PspQ/1756574872401.gif"

DEV_REPLIES = [
    "نورت الدنيا يا مبرمجي 🌟",
    "أهلاً بمبرمجي البوت 👨‍💻",
    "يا هلا يا مبرمجي العبقري 🔥",
    "حياك الله يا صاحب الموهبة يا مبرمجي 💫",
    "أيوه يا مبرمجي، أنا هنا خدمةً ليك 🤖",
    "وصل المبرمج، البوت في الخدمة 🚀",
    "يسلم إيدك يا مبرمجي على الشغل الجميل 💪",
]

NORMAL_REPLIES = [
    "أهلاً بيك يا فندم 😊",
    "نورت الجروب 🌟",
    "هلا والله 👋",
    "يا هلا يا نجم ✨",
    "حياك الله 🌹",
    "أيوه أيوه، كلنا سامعينك 😄",
    "إيه اللي تأمر بيه؟ 🎵",
]

BOT_REPLIES = [
    "آلة تكلم آلة 🤖",
    "بوت بيسلم على بوت، عالم غريب 😂",
    "أهلاً بالبوت الجديد 🤖",
    "بوت محترم، هيكون في الخدمة 🔧",
    "تحية من بوت لبوت 👾",
]


# ══════════════════════════
# دوال مساعدة
# ══════════════════════════

def is_dev(user_id):
    return user_id in DEV_IDS

def is_manager(chat_id, user_id):
    return bot_managers.get(chat_id, {}).get(user_id, False)

def is_muted(chat_id, user_id):
    return muted_users.get(chat_id, {}).get(user_id, False)

async def get_member_rank(client, chat_id, user_id):
    if is_dev(user_id):
        return "مبرمج"
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status == ChatMemberStatus.OWNER:
            return "مالك المجموعة"
        if is_manager(chat_id, user_id):
            return "مدير"
        if member.status == ChatMemberStatus.ADMINISTRATOR:
            return "مشرف"
        if getattr(member.user, 'is_bot', False):
            return "بوت"
        return "عضو"
    except:
        return "عضو"

async def can_mute(client, chat_id, muter_id, target_id):
    if is_dev(target_id):
        return False
    if is_dev(muter_id):
        return True
    try:
        muter = await client.get_chat_member(chat_id, muter_id)
        muter_rank = await get_member_rank(client, chat_id, muter_id)
        target_rank = await get_member_rank(client, chat_id, target_id)
        if muter.status == ChatMemberStatus.OWNER:
            return target_rank in ["مدير", "مشرف", "عضو"]
        if muter_rank == "مدير":
            return target_rank == "عضو"
    except:
        pass
    return False


# ══════════════════════════
# أول ما البوت يدخل جروب
# ══════════════════════════

@Client.on_message(filters.new_chat_members & filters.group)
async def on_bot_join(client: Client, message: Message):
    try:
        me = await client.get_me()
        for member in message.new_chat_members:
            if member.id == me.id:
                chat_id = message.chat.id
                if bot_managers.get(chat_id) is None:
                    bot_managers[chat_id] = {}
                async for m in client.get_chat_members(chat_id):
                    if m.status == ChatMemberStatus.ADMINISTRATOR and not m.user.is_bot:
                        bot_managers[chat_id][m.user.id] = True
                await message.reply(
                    "**✨ أهلاً بكم!**\n\n"
                    "🎵 أنا بوت الموسيقى، جاهز للخدمة!\n"
                    "📋 اكتب /الاوامر لتشاهد كل الأوامر المتاحة"
                )
    except:
        pass


# ══════════════════════════
# منع التصفية
# ══════════════════════════

@Client.on_chat_member_updated(filters.group)
async def track_bans(client: Client, update):
    try:
        if not (update.new_chat_member and
                update.new_chat_member.status == ChatMemberStatus.BANNED):
            return
        banner_id = update.from_user.id if update.from_user else None
        if not banner_id or is_dev(banner_id):
            return
        chat_id = update.chat.id
        if chat_id not in ban_count:
            ban_count[chat_id] = {}
        ban_count[chat_id][banner_id] = ban_count[chat_id].get(banner_id, 0) + 1
        count = ban_count[chat_id][banner_id]
        banned_user = update.new_chat_member.user
        banner = update.from_user
        await client.send_message(
            chat_id,
            f"⚠️ **إشعار حظر**\n\n"
            f"👮 **المشرف:** {banner.mention}\n"
            f"🚫 **حظر العضو:** {banned_user.mention}\n"
            f"📊 **عدد الحظرات:** `{count}/45`"
        )
        if count >= 45:
            try:
                await client.promote_chat_member(
                    chat_id, banner_id,
                    privileges=ChatPrivileges(
                        can_manage_chat=False,
                        can_delete_messages=False,
                        can_manage_video_chats=False,
                        can_restrict_members=False,
                        can_promote_members=False,
                        can_change_info=False,
                        can_invite_users=False,
                        can_pin_messages=False,
                    )
                )
                ban_count[chat_id][banner_id] = 0
                await client.send_message(
                    chat_id,
                    f"🚨 **تم إزالة المشرف من الإشراف!**\n\n"
                    f"👮 **المشرف:** {banner.mention}\n"
                    f"📊 **السبب:** تجاوز حد الحظر (45 حظر)"
                )
            except:
                pass
    except:
        pass


# ══════════════════════════
# حذف رسائل المكتومين
# ══════════════════════════

@Client.on_message(filters.group & filters.incoming, group=-1)
async def delete_muted_messages(client: Client, message: Message):
    if not message.from_user:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    if is_muted(chat_id, user_id):
        try:
            await message.delete()
        except:
            pass


# ══════════════════════════
# أوامر الكتم
# ══════════════════════════

async def do_mute(client, message, target_id, target_mention):
    chat_id = message.chat.id
    muter_id = message.from_user.id
    if not await can_mute(client, chat_id, muter_id, target_id):
        return await message.reply("❌ **مش مسموح ليك تكتم هذا المستخدم**")
    if muted_users.get(chat_id) is None:
        muted_users[chat_id] = {}
    muted_users[chat_id][target_id] = True
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔊 إلغاء الكتم", callback_data=f"unmute_{chat_id}_{target_id}")
    ]])
    await message.reply(
        f"🔇 **تم الكتم بنجاح**\n\n"
        f"👤 **المستخدم:** {target_mention}\n"
        f"📝 **سيتم حذف رسائله تلقائياً حتى إلغاء الكتم**",
        reply_markup=keyboard
    )


@Client.on_message(filters.group & command2(["كتم"]) & other_filters)
async def mute_user_cmd(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    muter_id = message.from_user.id
    rank = await get_member_rank(client, chat_id, muter_id)
    if rank not in ["مبرمج", "مالك المجموعة", "مدير"]:
        return
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
        await do_mute(client, message, target.id, target.mention)
    elif len(message.command) >= 2:
        arg = message.command[1]
        try:
            user = await client.get_users(arg.lstrip("@") if arg.startswith("@") else int(arg))
            await do_mute(client, message, user.id, user.mention)
        except:
            await message.reply("❌ **المستخدم مش موجود**")
    else:
        await message.reply("**الاستخدام:** /كتم بالرد أو /كتم @يوزر أو /كتم ID")


@Client.on_message(filters.group & command2(["الغاء_كتم", "فك_كتم"]) & other_filters)
async def unmute_user_cmd(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    user_id = message.from_user.id
    rank = await get_member_rank(client, chat_id, user_id)
    if rank not in ["مبرمج", "مالك المجموعة", "مدير"]:
        return
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    elif len(message.command) >= 2:
        arg = message.command[1]
        try:
            target = await client.get_users(arg.lstrip("@") if arg.startswith("@") else int(arg))
        except:
            return await message.reply("❌ **المستخدم مش موجود**")
    if target:
        if muted_users.get(chat_id):
            muted_users[chat_id].pop(target.id, None)
        await message.reply(f"🔊 **تم إلغاء كتم** {target.mention}")
    else:
        await message.reply("**الاستخدام:** /الغاء_كتم بالرد أو @يوزر أو ID")


@Client.on_callback_query(filters.regex(r"^unmute_(\-?\d+)_(\d+)$"))
async def cb_unmute(client: Client, query: CallbackQuery):
    parts = query.data.split("_")
    chat_id = int(parts[1])
    target_id = int(parts[2])
    user_id = query.from_user.id
    rank = await get_member_rank(client, chat_id, user_id)
    if rank not in ["مبرمج", "مالك المجموعة", "مدير"]:
        return await query.answer("❌ مش مسموح ليك إلغاء الكتم!", show_alert=True)
    if muted_users.get(chat_id):
        muted_users[chat_id].pop(target_id, None)
    try:
        target = await client.get_users(target_id)
        await query.message.edit_text(
            f"🔊 **تم إلغاء الكتم**\n\n"
            f"👤 **المستخدم:** {target.mention}\n"
            f"✅ **بواسطة:** {query.from_user.mention}"
        )
    except:
        await query.answer("✅ تم إلغاء الكتم", show_alert=True)


# ══════════════════════════
# أوامر الرفع والتنزيل
# ══════════════════════════

async def is_owner_or_dev(client, chat_id, user_id):
    if is_dev(user_id):
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status == ChatMemberStatus.OWNER
    except:
        return False


@Client.on_message(filters.group & command2(["رفع_مشرف"]) & other_filters)
async def promote_admin_cmd(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    user_id = message.from_user.id
    if not await is_owner_or_dev(client, chat_id, user_id):
        return
    # لو أمر رفع لازم يكون بعده "مشرف"
    if message.command[0] == "رفع":
        if len(message.command) < 2 or message.command[1] != "مشرف":
            return
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("**الاستخدام:** رد على المستخدم واكتب /رفع_مشرف [لقب]")
    target = message.reply_to_message.from_user
    title = " ".join(message.command[2:]) if len(message.command) > 2 else ""
    if message.command[0] == "رفع":
        title = " ".join(message.command[2:]) if len(message.command) > 2 else ""
    try:
        await client.promote_chat_member(
            chat_id, target.id,
            privileges=ChatPrivileges(
                can_manage_chat=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_restrict_members=True,
                can_invite_users=True,
                can_pin_messages=True,
            )
        )
        if title:
            try:
                await client.set_administrator_title(chat_id, target.id, title)
            except:
                pass
        await message.reply(
            f"✅ **تم الرفع بنجاح**\n\n"
            f"👤 **المشرف:** {target.mention}\n"
            f"🏷️ **اللقب:** `{title if title else 'بدون لقب'}`"
        )
    except Exception as e:
        await message.reply(f"❌ **فشل الرفع:** `{e}`")


@Client.on_message(filters.group & command2(["رفع_مدير"]) & other_filters)
async def promote_manager_cmd(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    user_id = message.from_user.id
    if not await is_owner_or_dev(client, chat_id, user_id):
        return
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    elif len(message.command) >= 2:
        arg = message.command[1]
        try:
            target = await client.get_users(arg.lstrip("@") if arg.startswith("@") else int(arg))
        except:
            return await message.reply("❌ المستخدم مش موجود")
    if not target:
        return await message.reply("**الاستخدام:** /رفع_مدير بالرد أو @يوزر أو ID")
    if bot_managers.get(chat_id) is None:
        bot_managers[chat_id] = {}
    bot_managers[chat_id][target.id] = True
    await message.reply(
        f"✅ **تم رفع مدير**\n\n"
        f"👤 **المدير:** {target.mention}\n"
        f"🔑 **الصلاحيات:** كتم الأعضاء"
    )


@Client.on_message(filters.group & command2(["تنزيل_مدير"]) & other_filters)
async def demote_manager_cmd(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    user_id = message.from_user.id
    if not await is_owner_or_dev(client, chat_id, user_id):
        return
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    elif len(message.command) >= 2:
        arg = message.command[1]
        try:
            target = await client.get_users(arg.lstrip("@") if arg.startswith("@") else int(arg))
        except:
            return await message.reply("❌ المستخدم مش موجود")
    if not target:
        return await message.reply("**الاستخدام:** /تنزيل_مدير بالرد أو @يوزر أو ID")
    if bot_managers.get(chat_id):
        bot_managers[chat_id].pop(target.id, None)
    await message.reply(f"✅ **تم تنزيل** {target.mention} **من رتبة المدير**")


@Client.on_message(filters.group & command2(["رفع_المشرفين"]) & other_filters)
async def promote_all_admins_cmd(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    user_id = message.from_user.id
    if not await is_owner_or_dev(client, chat_id, user_id):
        return
    if bot_managers.get(chat_id) is None:
        bot_managers[chat_id] = {}
    count = 0
    async for m in client.get_chat_members(chat_id):
        if m.status == ChatMemberStatus.ADMINISTRATOR and not m.user.is_bot:
            bot_managers[chat_id][m.user.id] = True
            count += 1
    await message.reply(
        f"✅ **تم رفع كل المشرفين مديرين**\n\n"
        f"👥 **العدد:** `{count}` مشرف"
    )


# ══════════════════════════
# رتبتي
# ══════════════════════════

@Client.on_message(filters.group & command2(["رتبتي"]) & other_filters)
async def my_rank_cmd(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    user_id = message.from_user.id
    rank = await get_member_rank(client, chat_id, user_id)
    rank_emoji = {
        "مبرمج": "👨‍💻",
        "مالك المجموعة": "👑",
        "مدير": "🔑",
        "مشرف": "⭐",
        "عضو": "👤",
        "بوت": "🤖",
    }
    emoji = rank_emoji.get(rank, "👤")
    await message.reply(
        f"**{emoji} رتبتك في البوت**\n\n"
        f"👤 **الاسم:** {message.from_user.mention}\n"
        f"🆔 **الأيدي:** `{user_id}`\n"
        f"🏅 **الرتبة:** `{rank}`"
    )


# ══════════════════════════
# مين في الكول / مين مشغل
# ══════════════════════════

@Client.on_message(filters.group & command2(["مين_في_الكول", "من_في_الكول", "الكول"]) & other_filters)
async def who_in_call_cmd(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    try:
        from driver.veez import call_py
        participants = await call_py.get_participants(chat_id)
        if not participants:
            return await message.reply("❌ **الكول فاضي دلوقتي**")
        text = "**🎤 المتواجدين في الكول:**\n\n"
        for i, p in enumerate(participants, 1):
            try:
                user = await client.get_users(p.user_id)
                text += f"`{i}.` [{user.first_name}](tg://user?id={user.id})\n"
            except:
                text += f"`{i}.` `{p.user_id}`\n"
        await message.reply(text, disable_web_page_preview=True)
    except:
        await message.reply("❌ **مفيش كول شغال دلوقتي**")


@Client.on_message(filters.group & command2(["مين_مشغل", "من_مشغل", "مشغل_ايه"]) & other_filters)
async def who_playing_cmd(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    if chat_id not in QUEUE or not QUEUE[chat_id]:
        return await message.reply("❌ **مفيش أغنية شغالة دلوقتي**")
    current = QUEUE[chat_id][0]
    songname = current[0]
    url = current[2]
    requester_info = song_requester.get(chat_id, {})
    requester = requester_info.get("mention", "غير معروف")
    await message.reply(
        f"**🎵 اللي شغال دلوقتي:**\n\n"
        f"🏷️ **الأغنية:** [{songname}]({url})\n"
        f"🎧 **طلبها:** {requester}"
    )


# ══════════════════════════
# الردود العشوائية
# ══════════════════════════

@Client.on_message(filters.group & filters.mentioned, group=2)
async def random_reply_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    if getattr(message.from_user, 'is_bot', False):
        reply = random.choice(BOT_REPLIES)
    elif is_dev(user_id):
        reply = random.choice(DEV_REPLIES)
    else:
        reply = random.choice(NORMAL_REPLIES)
    await message.reply(reply)


# ══════════════════════════
# ردود على البوتات
# ══════════════════════════

@Client.on_message(filters.group & filters.bot, group=3)
async def reply_to_bots(client: Client, message: Message):
    try:
        me = await client.get_me()
        if message.from_user and message.from_user.id != me.id:
            if random.random() < 0.3:  # 30% احتمال الرد عشان مش يزعج
                await message.reply(random.choice(BOT_REPLIES))
    except:
        pass


# ══════════════════════════
# أمر الاوامر
# ══════════════════════════

def get_commands_keyboard(category, user_id):
    back_btn = InlineKeyboardButton("🔙 رجوع", callback_data=f"cmds_main_{user_id}")
    if category == "main":
        rows = [
            [InlineKeyboardButton("🎵 التشغيل", callback_data=f"cmds_play_{user_id}"),
             InlineKeyboardButton("🛡️ الحماية", callback_data=f"cmds_protect_{user_id}")],
            [InlineKeyboardButton("👮 المشرفين", callback_data=f"cmds_admin_{user_id}")]
        ]
        if is_dev(user_id):
            rows.append([InlineKeyboardButton("👨‍💻 المبرمجين", callback_data=f"cmds_dev_{user_id}")])
        return InlineKeyboardMarkup(rows)
    if category == "play":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ /play - تشغيل أغنية", callback_data="cmd_ignore")],
            [InlineKeyboardButton("🎬 /vplay - تشغيل فيديو", callback_data="cmd_ignore")],
            [InlineKeyboardButton("⏭ /skip - تخطي", callback_data="cmd_ignore")],
            [InlineKeyboardButton("⏹ /stop - إيقاف", callback_data="cmd_ignore")],
            [InlineKeyboardButton("⏸ /pause - توقف مؤقت", callback_data="cmd_ignore")],
            [InlineKeyboardButton("▶️ /resume - استكمال", callback_data="cmd_ignore")],
            [InlineKeyboardButton("🔇 /mute - كتم الصوت", callback_data="cmd_ignore")],
            [InlineKeyboardButton("🔊 /unmute - رفع الكتم", callback_data="cmd_ignore")],
            [InlineKeyboardButton("🎵 /مين_مشغل", callback_data="cmd_ignore")],
            [InlineKeyboardButton("🎤 /مين_في_الكول", callback_data="cmd_ignore")],
            [back_btn]
        ])
    if category == "protect":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔇 /كتم - كتم مستخدم", callback_data="cmd_ignore")],
            [InlineKeyboardButton("🔊 /الغاء_كتم - إلغاء الكتم", callback_data="cmd_ignore")],
            [InlineKeyboardButton("🛡️ منع التصفية تلقائي (45 حظر)", callback_data="cmd_ignore")],
            [InlineKeyboardButton("🏅 /رتبتي - اعرف رتبتك", callback_data="cmd_ignore")],
            [back_btn]
        ])
    if category == "admin":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("👮 /رفع_مشرف [لقب]", callback_data="cmd_ignore")],
            [InlineKeyboardButton("🔑 /رفع_مدير", callback_data="cmd_ignore")],
            [InlineKeyboardButton("⬇️ /تنزيل_مدير", callback_data="cmd_ignore")],
            [InlineKeyboardButton("👥 /رفع_المشرفين", callback_data="cmd_ignore")],
            [InlineKeyboardButton("🔄 /reload - تحديث الأدمن", callback_data="cmd_ignore")],
            [back_btn]
        ])
    if category == "dev":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 /تحديث - تحديث البوت", callback_data="cmd_ignore")],
            [InlineKeyboardButton("🔁 /ريستارت - إعادة تشغيل", callback_data="cmd_ignore")],
            [InlineKeyboardButton("🚪 /مغادره البوت", callback_data="cmd_ignore")],
            [InlineKeyboardButton("📢 /broadcast - إرسال جماعي", callback_data="cmd_ignore")],
            [back_btn]
        ])
    return InlineKeyboardMarkup([[back_btn]])


def get_category_text(category):
    texts = {
        "main": "📋 **قائمة الأوامر**\n\nاختر الفئة اللي تريدها:",
        "play": "🎵 **أوامر التشغيل:**",
        "protect": "🛡️ **أوامر الحماية:**",
        "admin": "👮 **أوامر المشرفين والمديرين:**",
        "dev": "👨‍💻 **أوامر المبرمجين:**",
    }
    return texts.get(category, "📋 **الأوامر:**")


@Client.on_message(filters.group & command2(["الاوامر"]) & other_filters)
async def show_commands_cmd(client: Client, message: Message):
    await message.delete()
    user_id = message.from_user.id
    keyboard = get_commands_keyboard("main", user_id)
    await client.send_animation(
        message.chat.id,
        animation=GIF_URL,
        caption="📋 **قائمة الأوامر**\n\nاختر الفئة اللي تريدها:",
        reply_markup=keyboard
    )


@Client.on_callback_query(filters.regex(r"^cmds_(\w+)_(\d+)$"))
async def commands_callback(client: Client, query: CallbackQuery):
    parts = query.data.split("_")
    category = parts[1]
    owner_id = int(parts[2])
    if query.from_user.id != owner_id:
        return await query.answer("❌ هذه القائمة مش ليك!", show_alert=True)
    if category == "dev" and not is_dev(query.from_user.id):
        return await query.answer("❌ هذه الأوامر للمبرمجين فقط!", show_alert=True)
    keyboard = get_commands_keyboard(category, owner_id)
    text = get_category_text(category)
    try:
        await query.message.edit_caption(caption=text, reply_markup=keyboard)
    except:
        await query.answer()


@Client.on_callback_query(filters.regex("^cmd_ignore$"))
async def cmd_ignore_cb(client: Client, query: CallbackQuery):
    await query.answer()
