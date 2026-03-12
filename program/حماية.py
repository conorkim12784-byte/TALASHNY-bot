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
from driver.filters import other_filters
from driver.queues import QUEUE

# ═══════════════════════════════════════
# 🔧 إعدادات وثوابت
# ═══════════════════════════════════════

DEV_IDS = [1923931101, 5340100457]

# تخزين عدد الحظرات لكل مشرف في كل جروب
ban_count = {}  # {chat_id: {user_id: count}}

# تخزين المكتومين في كل جروب
muted_users = {}  # {chat_id: {user_id: True}}

# تخزين المديرين في البوت
bot_managers = {}  # {chat_id: {user_id: True}}

# تخزين اللي طلبوا الأغاني
song_requester = {}  # {chat_id: {"name": ..., "requester": ...}}

GIF_URL = "https://i.postimg.cc/wxV3PspQ/1756574872401.gif"

# ردود عشوائية للأيديين (فيها مبرمجي)
DEV_REPLIES = [
    "نورت الدنيا يا مبرمجي 🌟",
    "أهلاً بمبرمجي البوت 👨‍💻",
    "يا هلا يا مبرمجي العبقري 🔥",
    "حياك الله يا صاحب الموهبة يا مبرمجي 💫",
    "أيوه يا مبرمجي، أنا هنا خدمةً ليك 🤖",
    "وصل المبرمج، البوت في الخدمة 🚀",
    "يسلم إيدك يا مبرمجي على الشغل الجميل 💪",
]

# ردود عشوائية للأعضاء العاديين
NORMAL_REPLIES = [
    "أهلاً بيك يا فندم 😊",
    "نورت الجروب 🌟",
    "هلا والله 👋",
    "يا هلا يا نجم ✨",
    "حياك الله 🌹",
    "أيوه أيوه، كلنا سامعينك 😄",
    "إيه اللي تأمر بيه؟ 🎵",
]

# ردود على البوتات
BOT_REPLIES = [
    "آلة تكلم آلة 🤖",
    "بوت بيسلم على بوت، عالم غريب 😂",
    "أهلاً بالبوت الجديد 🤖",
    "بوت محترم، هيكون في الخدمة 🔧",
    "تحية من بوت لبوت 👾",
]


# ═══════════════════════════════════════
# 🔍 دوال مساعدة
# ═══════════════════════════════════════

def is_dev(user_id):
    return user_id in DEV_IDS

def is_manager(chat_id, user_id):
    return bot_managers.get(chat_id, {}).get(user_id, False)

def is_muted(chat_id, user_id):
    return muted_users.get(chat_id, {}).get(user_id, False)

async def get_member_rank(client, chat_id, user_id):
    """يرجع رتبة المستخدم"""
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
        if member.status == ChatMemberStatus.MEMBER:
            return "عضو"
        if member.user.is_bot:
            return "بوت"
    except:
        pass
    return "عضو"

async def can_mute(client, chat_id, muter_id, target_id):
    """يتحقق إذا المستخدم يقدر يكتم الهدف"""
    if is_dev(muter_id) and not is_dev(target_id):
        return True
    try:
        muter = await client.get_chat_member(chat_id, muter_id)
        target = await client.get_chat_member(chat_id, target_id)
        muter_rank = await get_member_rank(client, chat_id, muter_id)
        target_rank = await get_member_rank(client, chat_id, target_id)
        # المالك يكتم المديرين والمشرفين والأعضاء بس مش الأيديين
        if muter.status == ChatMemberStatus.OWNER:
            if is_dev(target_id):
                return False
            if target_rank in ["مدير", "مشرف", "عضو"]:
                return True
        # المدير يكتم الأعضاء بس
        if muter_rank == "مدير":
            if target_rank == "عضو":
                return True
            return False
    except:
        pass
    return False


# ═══════════════════════════════════════
# 🚀 أول ما البوت يدخل جروب
# ═══════════════════════════════════════

@Client.on_message(filters.new_chat_members & filters.group)
async def on_bot_join(client: Client, message: Message):
    me = await client.get_me()
    for member in message.new_chat_members:
        if member.id == me.id:
            chat_id = message.chat.id
            try:
                # رفع المالك مالك في البوت
                chat = await client.get_chat(chat_id)
                if chat.permissions:
                    pass
                # رفع المشرفين مديرين في البوت
                async for m in client.get_chat_members(chat_id):
                    if m.status == ChatMemberStatus.ADMINISTRATOR:
                        if bot_managers.get(chat_id) is None:
                            bot_managers[chat_id] = {}
                        bot_managers[chat_id][m.user.id] = True
                await message.reply(
                    "**✨ أهلاً بكم!**\n\n"
                    "🎵 أنا بوت الموسيقى، جاهز للخدمة!\n"
                    "📋 اكتب /الاوامر لتشاهد كل الأوامر المتاحة"
                )
            except Exception as e:
                pass


# ═══════════════════════════════════════
# 🛡️ منع التصفية - مراقبة الحظرات
# ═══════════════════════════════════════

@Client.on_message(filters.group & filters.service)
async def anti_flood_ban(client: Client, message: Message):
    try:
        if not message.new_chat_members and not hasattr(message, 'left_chat_member'):
            return
    except:
        pass


@Client.on_chat_member_updated(filters.group)
async def track_bans(client: Client, update):
    try:
        chat_id = update.chat.id
        if update.new_chat_member and update.new_chat_member.status == ChatMemberStatus.BANNED:
            banner_id = update.from_user.id if update.from_user else None
            if not banner_id:
                return
            if is_dev(banner_id):
                return
            # زود العداد
            if chat_id not in ban_count:
                ban_count[chat_id] = {}
            ban_count[chat_id][banner_id] = ban_count[chat_id].get(banner_id, 0) + 1
            count = ban_count[chat_id][banner_id]
            banned_user = update.new_chat_member.user
            banner = update.from_user
            # إشعار بكل حظر
            await client.send_message(
                chat_id,
                f"⚠️ **إشعار حظر**\n\n"
                f"👮 **المشرف:** {banner.mention}\n"
                f"🚫 **حظر العضو:** {banned_user.mention}\n"
                f"📊 **عدد الحظرات:** `{count}/45`"
            )
            # لو وصل 45 ينزله
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
                except Exception as e:
                    pass
    except Exception as e:
        pass


# ═══════════════════════════════════════
# 🔇 نظام الكتم
# ═══════════════════════════════════════

@Client.on_message(filters.group & filters.incoming)
async def delete_muted_messages(client: Client, message: Message):
    """حذف رسائل المكتومين تلقائياً"""
    if not message.from_user:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    if is_muted(chat_id, user_id):
        try:
            await message.delete()
        except:
            pass


async def do_mute(client, message, target_id, target_name):
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
        f"👤 **المستخدم:** {target_name}\n"
        f"📝 **سيتم حذف رسائله تلقائياً حتى إلغاء الكتم**",
        reply_markup=keyboard
    )


@Client.on_message(filters.group & filters.command(["كتم", "mute_user"]) & other_filters)
async def mute_user(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    muter_id = message.from_user.id
    muter_rank = await get_member_rank(client, chat_id, muter_id)
    if muter_rank not in ["مبرمج", "مالك المجموعة", "مدير"]:
        return
    target = None
    target_name = ""
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
        target_name = target.mention
        await do_mute(client, message, target.id, target_name)
    elif len(message.command) >= 2:
        arg = message.command[1]
        try:
            if arg.startswith("@"):
                user = await client.get_users(arg)
            else:
                user = await client.get_users(int(arg))
            target_name = user.mention
            await do_mute(client, message, user.id, target_name)
        except:
            await message.reply("❌ **المستخدم مش موجود**")
    else:
        await message.reply("**الاستخدام:** /كتم بالرد أو /كتم @يوزر أو /كتم ID")


@Client.on_message(filters.group & filters.command(["الغاء_كتم", "فك_كتم"]) & other_filters)
async def unmute_user(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    muter_id = message.from_user.id
    muter_rank = await get_member_rank(client, chat_id, muter_id)
    if muter_rank not in ["مبرمج", "مالك المجموعة", "مدير"]:
        return
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    elif len(message.command) >= 2:
        arg = message.command[1]
        try:
            if arg.startswith("@"):
                target = await client.get_users(arg)
            else:
                target = await client.get_users(int(arg))
        except:
            return await message.reply("❌ **المستخدم مش موجود**")
    if target:
        if muted_users.get(chat_id):
            muted_users[chat_id].pop(target.id, None)
        await message.reply(f"🔊 **تم إلغاء كتم** {target.mention}")
    else:
        await message.reply("**الاستخدام:** /الغاء_كتم بالرد أو /الغاء_كتم @يوزر أو ID")


@Client.on_callback_query(filters.regex(r"^unmute_(\-?\d+)_(\d+)$"))
async def cb_unmute(client: Client, query: CallbackQuery):
    chat_id = int(query.data.split("_")[1])
    target_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    rank = await get_member_rank(client, chat_id, user_id)
    if rank not in ["مبرمج", "مالك المجموعة", "مدير"]:
        return await query.answer("❌ مش مسموح ليك إلغاء الكتم!", show_alert=True)
    if muted_users.get(chat_id):
        muted_users[chat_id].pop(target_id, None)
    try:
        target = await client.get_users(target_id)
        await query.message.edit_text(
            f"🔊 **تم إلغاء الكتم**\n\n👤 **المستخدم:** {target.mention}\n✅ **بواسطة:** {query.from_user.mention}"
        )
    except:
        await query.answer("✅ تم إلغاء الكتم", show_alert=True)


# ═══════════════════════════════════════
# 👑 أوامر الرفع والتنزيل
# ═══════════════════════════════════════

@Client.on_message(filters.group & filters.regex(r"^[/!.](رفع مشرف|رفع_مشرف)") & other_filters)
async def promote_admin(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    user_id = message.from_user.id
    # المالك والأيديين بس
    member = await client.get_chat_member(chat_id, user_id)
    if not is_dev(user_id) and member.status != ChatMemberStatus.OWNER:
        return
    target = None
    title = ""
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
        parts = message.text.split(None, 2)
        title = parts[2] if len(parts) > 2 else ""
    else:
        return await message.reply("**الاستخدام:** /رفع مشرف [لقب] بالرد على المستخدم")
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
            await client.set_administrator_title(chat_id, target.id, title)
        await message.reply(
            f"✅ **تم الرفع بنجاح**\n\n"
            f"👤 **المشرف:** {target.mention}\n"
            f"🏷️ **اللقب:** `{title if title else 'بدون لقب'}`"
        )
    except Exception as e:
        await message.reply(f"❌ **فشل الرفع:** `{e}`")


@Client.on_message(filters.group & filters.regex(r"^[/!.](رفع مدير|رفع_مدير)") & other_filters)
async def promote_manager(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    user_id = message.from_user.id
    member = await client.get_chat_member(chat_id, user_id)
    if not is_dev(user_id) and member.status != ChatMemberStatus.OWNER:
        return
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    elif len(message.command) >= 2:
        try:
            arg = message.command[1]
            if arg.startswith("@"):
                target = await client.get_users(arg)
            else:
                target = await client.get_users(int(arg))
        except:
            return await message.reply("❌ المستخدم مش موجود")
    if not target:
        return await message.reply("**الاستخدام:** /رفع مدير بالرد أو @يوزر أو ID")
    if bot_managers.get(chat_id) is None:
        bot_managers[chat_id] = {}
    bot_managers[chat_id][target.id] = True
    await message.reply(
        f"✅ **تم رفع مدير**\n\n"
        f"👤 **المدير:** {target.mention}\n"
        f"🔑 **الصلاحيات:** كتم الأعضاء"
    )


@Client.on_message(filters.group & filters.regex(r"^[/!.](تنزيل مدير|تنزيل_مدير)") & other_filters)
async def demote_manager(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    user_id = message.from_user.id
    member = await client.get_chat_member(chat_id, user_id)
    if not is_dev(user_id) and member.status != ChatMemberStatus.OWNER:
        return
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    elif len(message.command) >= 2:
        try:
            arg = message.command[1]
            if arg.startswith("@"):
                target = await client.get_users(arg)
            else:
                target = await client.get_users(int(arg))
        except:
            return await message.reply("❌ المستخدم مش موجود")
    if not target:
        return await message.reply("**الاستخدام:** /تنزيل مدير بالرد أو @يوزر أو ID")
    if bot_managers.get(chat_id):
        bot_managers[chat_id].pop(target.id, None)
    await message.reply(f"✅ **تم تنزيل** {target.mention} **من رتبة المدير**")


@Client.on_message(filters.group & filters.regex(r"^[/!.](رفع المشرفين|رفع_المشرفين)") & other_filters)
async def promote_all_admins(client: Client, message: Message):
    await message.delete()
    chat_id = message.chat.id
    user_id = message.from_user.id
    member = await client.get_chat_member(chat_id, user_id)
    if not is_dev(user_id) and member.status != ChatMemberStatus.OWNER:
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


@Client.on_message(filters.group & filters.regex(r"^[/!.](رفع مشرف|رفع_مشرف)") & other_filters)
async def promote_from_file(client: Client, message: Message):
    """أمر الرفع المدمج من ملف الرفع"""
    pass


# ═══════════════════════════════════════
# 🏅 أمر رتبتي
# ═══════════════════════════════════════

@Client.on_message(filters.group & filters.command(["رتبتي"]) & other_filters)
async def my_rank(client: Client, message: Message):
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


# ═══════════════════════════════════════
# 🎤 مين في الكول ومين مشغل
# ═══════════════════════════════════════

@Client.on_message(filters.group & filters.command(["مين_في_الكول", "من_في_الكول", "الكول"]) & other_filters)
async def who_in_call(client: Client, message: Message):
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
    except Exception as e:
        await message.reply(f"❌ **مفيش كول شغال دلوقتي**")


@Client.on_message(filters.group & filters.command(["مين_مشغل", "من_مشغل", "مشغل_ايه"]) & other_filters)
async def who_playing(client: Client, message: Message):
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


# ═══════════════════════════════════════
# 💬 الردود العشوائية
# ═══════════════════════════════════════

@Client.on_message(filters.group & filters.mentioned)
async def random_reply(client: Client, message: Message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    if message.from_user.is_bot:
        reply = random.choice(BOT_REPLIES)
    elif is_dev(user_id):
        reply = random.choice(DEV_REPLIES)
    else:
        reply = random.choice(NORMAL_REPLIES)
    await message.reply(reply)


# ═══════════════════════════════════════
# 📋 أمر الاوامر مع GIF وأزرار
# ═══════════════════════════════════════

def get_commands_keyboard(category, user_id):
    """يرجع الكيبورد حسب الفئة"""
    buttons = []
    if category == "main":
        rows = [
            [InlineKeyboardButton("🎵 التشغيل", callback_data=f"cmds_play_{user_id}"),
             InlineKeyboardButton("🛡️ الحماية", callback_data=f"cmds_protect_{user_id}")],
            [InlineKeyboardButton("👮 المشرفين", callback_data=f"cmds_admin_{user_id}")]
        ]
        if is_dev(user_id):
            rows.append([InlineKeyboardButton("👨‍💻 المبرمجين", callback_data=f"cmds_dev_{user_id}")])
        return InlineKeyboardMarkup(rows)

    back_btn = InlineKeyboardButton("🔙 رجوع", callback_data=f"cmds_main_{user_id}")

    if category == "play":
        buttons = [
            [InlineKeyboardButton("▶️ /play - تشغيل أغنية", callback_data="ignore")],
            [InlineKeyboardButton("🎬 /vplay - تشغيل فيديو", callback_data="ignore")],
            [InlineKeyboardButton("⏭ /skip - تخطي", callback_data="ignore")],
            [InlineKeyboardButton("⏹ /stop - إيقاف", callback_data="ignore")],
            [InlineKeyboardButton("⏸ /pause - توقف مؤقت", callback_data="ignore")],
            [InlineKeyboardButton("▶️ /resume - استكمال", callback_data="ignore")],
            [InlineKeyboardButton("🔇 /mute - كتم الصوت", callback_data="ignore")],
            [InlineKeyboardButton("🔊 /unmute - رفع الكتم", callback_data="ignore")],
            [InlineKeyboardButton("🎵 /مين_مشغل - مين شغال إيه", callback_data="ignore")],
            [InlineKeyboardButton("🎤 /مين_في_الكول - من في الكول", callback_data="ignore")],
            [back_btn]
        ]
    elif category == "protect":
        buttons = [
            [InlineKeyboardButton("🔇 /كتم - كتم مستخدم", callback_data="ignore")],
            [InlineKeyboardButton("🔊 /الغاء_كتم - إلغاء الكتم", callback_data="ignore")],
            [InlineKeyboardButton("🛡️ منع التصفية تلقائي", callback_data="ignore")],
            [InlineKeyboardButton("🏅 /رتبتي - اعرف رتبتك", callback_data="ignore")],
            [back_btn]
        ]
    elif category == "admin":
        buttons = [
            [InlineKeyboardButton("👮 /رفع مشرف [لقب]", callback_data="ignore")],
            [InlineKeyboardButton("🔑 /رفع مدير", callback_data="ignore")],
            [InlineKeyboardButton("⬇️ /تنزيل مدير", callback_data="ignore")],
            [InlineKeyboardButton("👥 /رفع المشرفين", callback_data="ignore")],
            [InlineKeyboardButton("🔄 /reload - تحديث الأدمن", callback_data="ignore")],
            [back_btn]
        ]
    elif category == "dev":
        buttons = [
            [InlineKeyboardButton("🔄 /تحديث - تحديث البوت", callback_data="ignore")],
            [InlineKeyboardButton("🔁 /ريستارت - إعادة تشغيل", callback_data="ignore")],
            [InlineKeyboardButton("🚪 /مغادره البوت", callback_data="ignore")],
            [InlineKeyboardButton("📢 /broadcast - إرسال جماعي", callback_data="ignore")],
            [back_btn]
        ]
    return InlineKeyboardMarkup(buttons)


def get_category_text(category):
    texts = {
        "main": "📋 **قائمة الأوامر**\n\nاختر الفئة اللي تريدها:",
        "play": "🎵 **أوامر التشغيل:**",
        "protect": "🛡️ **أوامر الحماية:**",
        "admin": "👮 **أوامر المشرفين والمديرين:**",
        "dev": "👨‍💻 **أوامر المبرمجين:**",
    }
    return texts.get(category, "📋 **الأوامر:**")


@Client.on_message(filters.group & filters.command(["الاوامر", "commands", "help"]) & other_filters)
async def show_commands(client: Client, message: Message):
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
    data_parts = query.data.split("_")
    category = data_parts[1]
    owner_id = int(data_parts[2])
    # بس اللي طلب الأمر يقدر يتنقل
    if query.from_user.id != owner_id:
        return await query.answer("❌ هذه القائمة مش ليك!", show_alert=True)
    if category == "dev" and not is_dev(query.from_user.id):
        return await query.answer("❌ هذه الأوامر للمبرمجين فقط!", show_alert=True)
    keyboard = get_commands_keyboard(category, owner_id)
    text = get_category_text(category)
    await query.message.edit_caption(caption=text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex("^ignore$"))
async def ignore_cb(client: Client, query: CallbackQuery):
    await query.answer()
