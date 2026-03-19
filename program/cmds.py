# cmds.py — قائمة الأوامر الموحدة

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from driver.filters import command, command2, other_filters
from config import BOT_NAME, BOT_PHOTO, UPDATES_CHANNEL, GROUP_SUPPORT, SUDO_USERS

GIF_URL = "https://i.postimg.cc/wxV3PspQ/1756574872401.gif"

MAIN_CAPTION = """**╭────⌁TALASHNY⌁────⟤
│╭───────────⟢
╞╡       قائمة الأوامر
╞╡
╞╡  اختر القسم اللي تريده
│╰────────────╮
│╭────────────╯
╞╡   استمتع بتجربة مميزة
│╰───────────⟢
╰────⌁TALASHNY⌁────⟤**"""


def main_keyboard(user_id: int):
    rows = [
        [
            InlineKeyboardButton("🎵 الأعضاء", callback_data="cmds_members"),
            InlineKeyboardButton("🛡️ المشرفين", callback_data="cmds_admins"),
        ],
        [InlineKeyboardButton("👑 المالك", callback_data="cmds_owner")],
    ]
    if user_id in SUDO_USERS:
        rows.append([InlineKeyboardButton("⚙️ المطور", callback_data="cmds_dev")])
    rows.append([InlineKeyboardButton("✖ إغلاق", callback_data="cmds_close")])
    return InlineKeyboardMarkup(rows)


def section_keyboard(user_id: int, section: str):
    """كيبورد داخل كل قسم — عربي / انجليزي + رجوع"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇸🇦 عربي", callback_data=f"{section}_ar"),
            InlineKeyboardButton("🇬🇧 English", callback_data=f"{section}_en"),
        ],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"cmds_back_{user_id}")],
        [InlineKeyboardButton("✖ إغلاق", callback_data="cmds_close")],
    ])


def back_keyboard(user_id: int, section: str):
    """كيبورد في صفحة الأوامر — زرار رجوع للقسم"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"cmds_{section}")],
        [InlineKeyboardButton("✖ إغلاق", callback_data="cmds_close")],
    ])


# ═══════════════════════════════════════
# نصوص الأوامر
# ═══════════════════════════════════════

MEMBERS_AR = """**🎵 أوامر الأعضاء — عربي**

**▸ تشغيل موسيقى:**
`تشغيل` — تشغيل أغنية باسمها أو رابط
`شغل` — نفس تشغيل

**▸ تشغيل فيديو:**
`فيد` — تشغيل فيديو
`فيديو` — نفس فيد

**▸ بحث وتحميل:**
`بحث` — بحث عن أغنية
`يوت` — بحث على يوتيوب
`تحميل` — تحميل أغنية كملف صوتي
`تحميل فيديو` — تحميل فيديو كملف

**▸ معلومات:**
`مشغل` — الأغنية الشغالة دلوقتي
`الان` — نفس مشغل
`في الكول` — مين في الكول
`كول` — نفس في الكول
`قايمة` — قايمة الأغاني
`مده التشغيل` — وقت التشغيل الحالي
`ايدي` — عرض الـ ID

**▸ عام:**
`بينج` — سرعة البوت"""

MEMBERS_EN = """**🎵 Members Commands — English**

**▸ Play Music:**
`play` — play a song by name or link
`mplay` — same as play

**▸ Play Video:**
`vplay` — play a video
`vstream` — stream a direct link

**▸ Search & Download:**
`search` — search for a song
`song` — download song as audio file
`vsong` — download video as file
`video` — same as vsong

**▸ Info:**
`np` — currently playing song
`nowplaying` — same as np
`incall` — who is in the call
`queue` — songs queue
`playlist` — same as queue
`id` — show user/chat ID

**▸ General:**
`ping` — bot speed
`uptime` — bot uptime"""

ADMINS_AR = """**🛡️ أوامر المشرفين — عربي**

**▸ التحكم في التشغيل:**
`تخطي` — تخطي الأغنية الحالية
`انهاء` — إيقاف التشغيل ومغادرة الكول
`اسكت` — نفس انهاء
`ايقاف` — إيقاف مؤقت
`كمل` — استكمال بعد الإيقاف
`ميوت` — كتم صوت البوت
`فك ميوت` — رفع الكتم
`تحكم` — التحكم في مستوى الصوت (1-200)
`صوت` — نفس تحكم

**▸ إدارة الأعضاء:**
`كتم` — رد على رسالة لكتم عضو
`فك كتم` — رد على رسالة لفك الكتم"""

ADMINS_EN = """**🛡️ Admins Commands — English**

**▸ Playback Control:**
`skip` — skip current song
`stop` — stop and leave call
`pause` — pause playback
`resume` — resume playback
`mute` — mute the bot
`unmute` — unmute the bot"""

OWNER_AR = """**👑 أوامر المالك — عربي**

**▸ إدارة المشرفين:**
`رفع` — رفع عضو مشرف (رد أو ذكر)
`رفع مشرف` — نفس رفع
`رفع بوت` — رفع البوت مشرف
`بوت ادمن` — نفس رفع بوت
`شيل بوت ادمن` — تنزيل البوت من المشرفين
`قايمة الادمنز` — عرض قائمة المديرين
`اعاده` — تحديث قائمة المشرفين
`تحديث الادمن` — نفس اعاده

**▸ القفل والفتح:**
`قفل` — قفل الجروب (صور/روابط/دردشة/الكل)
`فتح` — فتح الجروب

**▸ متنوع:**
`تحديث` — تحديث البوت
`ريستارت` — إعادة تشغيل البوت
`سيرفر` — معلومات السيرفر
`حد الحظر` — تحديد حد الحظر التلقائي"""

OWNER_EN = """**👑 Owner Commands — English**

**▸ Admin Management:**
`promote` — promote a member to admin
`botadmin` — promote bot to admin
`rmbotadmin` — demote bot from admins
`setbanlimit` — set auto-ban limit

**▸ Misc:**
`update` — update the bot
`restart` — restart the bot
`sysinfo` — server information
`uptime` — bot uptime"""

DEV_AR = """**⚙️ أوامر المطور — عربي**

**▸ تنفيذ:**
`eval` — تنفيذ كود Python
`sh` — تنفيذ أمر Shell

**▸ إدارة البوت:**
`اذاعه` — إرسال رسالة لكل الجروبات
`ذت` — إذاعة مع تثبيت
`leaveall` — مغادرة كل الجروبات
`مغادره البوت` — مغادرة جروب معين

**▸ تنظيف السيرفر:**
`rmd` — حذف الملفات المحملة
`rmw` — حذف ملفات raw
`cleanup` — تنظيف شامل"""

DEV_EN = """**⚙️ Developer Commands — English**

**▸ Execute:**
`eval` — execute Python code
`sh` — execute Shell command

**▸ Bot Management:**
`broadcast` — send message to all groups
`leaveall` — leave all groups
`leavebot` — leave a specific group

**▸ Cleanup:**
`rmd` / `clear` — delete downloaded files
`rmw` / `clean` — delete raw files
`cleanup` — full cleanup"""


def cmds_text_keyboard(text: str, user_id: int, section: str):
    """بيحول النص لأزرار نسخ + نص"""
    lines = text.strip().split("\n")
    buttons = []
    for line in lines:
        line = line.strip()
        # لو السطر فيه أمر (بيبدأ بـ backtick)
        if line.startswith("`") and "`" in line[1:]:
            cmd = line.split("`")[1]
            desc = line.split("`", 2)[-1].strip(" —-")
            buttons.append([
                InlineKeyboardButton(f"📋 {cmd}", switch_inline_query_current_chat=cmd),
            ])
    buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"cmds_{section}")])
    buttons.append([InlineKeyboardButton("✖ إغلاق", callback_data="cmds_close")])
    return text, InlineKeyboardMarkup(buttons)


# ═══════════════════════════════════════
# الأوامر
# ═══════════════════════════════════════

@Client.on_message(
    (command(["commands", "cmds", "help"]) | command2(["الاوامر", "اوامر"])) & other_filters
)
async def show_commands(c: Client, m: Message):
    await m.delete()
    user_id = m.from_user.id
    try:
        await c.send_animation(
            m.chat.id,
            animation=GIF_URL,
            caption=MAIN_CAPTION,
            reply_markup=main_keyboard(user_id)
        )
    except Exception:
        await m.reply(MAIN_CAPTION, reply_markup=main_keyboard(user_id))


@Client.on_message(command(["help", "h"]) & filters.private)
async def help_private(c: Client, m: Message):
    user_id = m.from_user.id
    try:
        await m.reply_photo(
            photo=BOT_PHOTO,
            caption=MAIN_CAPTION,
            reply_markup=main_keyboard(user_id)
        )
    except Exception:
        await m.reply(MAIN_CAPTION, reply_markup=main_keyboard(user_id))


# ── قسم الأعضاء ──
@Client.on_callback_query(filters.regex("^cmds_members$"))
async def cmds_members(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    kb = section_keyboard(user_id, "members")
    try:
        await query.edit_message_caption("**🎵 أوامر الأعضاء**\n\nاختار اللغة:", reply_markup=kb)
    except Exception:
        await query.edit_message_text("**🎵 أوامر الأعضاء**\n\nاختار اللغة:", reply_markup=kb)
    await query.answer()

@Client.on_callback_query(filters.regex("^members_ar$"))
async def members_ar(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    kb = back_keyboard(user_id, "members")
    try:
        await query.edit_message_caption(MEMBERS_AR, reply_markup=kb)
    except Exception:
        await query.edit_message_text(MEMBERS_AR, reply_markup=kb)
    await query.answer()

@Client.on_callback_query(filters.regex("^members_en$"))
async def members_en(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    kb = back_keyboard(user_id, "members")
    try:
        await query.edit_message_caption(MEMBERS_EN, reply_markup=kb)
    except Exception:
        await query.edit_message_text(MEMBERS_EN, reply_markup=kb)
    await query.answer()


# ── قسم المشرفين ──
@Client.on_callback_query(filters.regex("^cmds_admins$"))
async def cmds_admins_cb(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    kb = section_keyboard(user_id, "admins")
    try:
        await query.edit_message_caption("**🛡️ أوامر المشرفين**\n\nاختار اللغة:", reply_markup=kb)
    except Exception:
        await query.edit_message_text("**🛡️ أوامر المشرفين**\n\nاختار اللغة:", reply_markup=kb)
    await query.answer()

@Client.on_callback_query(filters.regex("^admins_ar$"))
async def admins_ar(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    kb = back_keyboard(user_id, "admins")
    try:
        await query.edit_message_caption(ADMINS_AR, reply_markup=kb)
    except Exception:
        await query.edit_message_text(ADMINS_AR, reply_markup=kb)
    await query.answer()

@Client.on_callback_query(filters.regex("^admins_en$"))
async def admins_en(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    kb = back_keyboard(user_id, "admins")
    try:
        await query.edit_message_caption(ADMINS_EN, reply_markup=kb)
    except Exception:
        await query.edit_message_text(ADMINS_EN, reply_markup=kb)
    await query.answer()


# ── قسم المالك ──
@Client.on_callback_query(filters.regex("^cmds_owner$"))
async def cmds_owner_cb(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    kb = section_keyboard(user_id, "owner")
    try:
        await query.edit_message_caption("**👑 أوامر المالك**\n\nاختار اللغة:", reply_markup=kb)
    except Exception:
        await query.edit_message_text("**👑 أوامر المالك**\n\nاختار اللغة:", reply_markup=kb)
    await query.answer()

@Client.on_callback_query(filters.regex("^owner_ar$"))
async def owner_ar(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    kb = back_keyboard(user_id, "owner")
    try:
        await query.edit_message_caption(OWNER_AR, reply_markup=kb)
    except Exception:
        await query.edit_message_text(OWNER_AR, reply_markup=kb)
    await query.answer()

@Client.on_callback_query(filters.regex("^owner_en$"))
async def owner_en(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    kb = back_keyboard(user_id, "owner")
    try:
        await query.edit_message_caption(OWNER_EN, reply_markup=kb)
    except Exception:
        await query.edit_message_text(OWNER_EN, reply_markup=kb)
    await query.answer()


# ── قسم المطور ──
@Client.on_callback_query(filters.regex("^cmds_dev$"))
async def cmds_dev_cb(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in SUDO_USERS:
        await query.answer("❌ هذا القسم للمطور فقط", show_alert=True)
        return
    kb = section_keyboard(user_id, "dev")
    try:
        await query.edit_message_caption("**⚙️ أوامر المطور**\n\nاختار اللغة:", reply_markup=kb)
    except Exception:
        await query.edit_message_text("**⚙️ أوامر المطور**\n\nاختار اللغة:", reply_markup=kb)
    await query.answer()

@Client.on_callback_query(filters.regex("^dev_ar$"))
async def dev_ar(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in SUDO_USERS:
        await query.answer("❌ للمطور فقط", show_alert=True)
        return
    kb = back_keyboard(user_id, "dev")
    try:
        await query.edit_message_caption(DEV_AR, reply_markup=kb)
    except Exception:
        await query.edit_message_text(DEV_AR, reply_markup=kb)
    await query.answer()

@Client.on_callback_query(filters.regex("^dev_en$"))
async def dev_en(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in SUDO_USERS:
        await query.answer("❌ للمطور فقط", show_alert=True)
        return
    kb = back_keyboard(user_id, "dev")
    try:
        await query.edit_message_caption(DEV_EN, reply_markup=kb)
    except Exception:
        await query.edit_message_text(DEV_EN, reply_markup=kb)
    await query.answer()


# ── رجوع للرئيسية ──
@Client.on_callback_query(filters.regex(r"^cmds_back_(\d+)$"))
async def cmds_back(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    try:
        await query.edit_message_caption(MAIN_CAPTION, reply_markup=main_keyboard(user_id))
    except Exception:
        await query.edit_message_text(MAIN_CAPTION, reply_markup=main_keyboard(user_id))
    await query.answer()


# ── إغلاق ──
@Client.on_callback_query(filters.regex("^cmds_close$"))
async def cmds_close(c: Client, query: CallbackQuery):
    await query.message.delete()
    await query.answer()
