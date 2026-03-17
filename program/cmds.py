# cmds.py — قائمة الأوامر الموحدة

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from driver.filters import command, command2, other_filters
from config import BOT_NAME, BOT_PHOTO, UPDATES_CHANNEL, GROUP_SUPPORT, SUDO_USERS

GIF_URL = "https://i.postimg.cc/wxV3PspQ/1756574872401.gif"

MEMBERS_TEXT = """**🎵 أوامر الأعضاء**

**تشغيل موسيقى:**
» `تشغيل` / `شغل` + اسم الأغنية أو رابط
» `play` / `mplay` + اسم الأغنية

**تشغيل فيديو:**
» `فيد` / `فيديو` / `vplay` + اسم أو رابط
» `ستريم` / `vstream` + رابط مباشر

**معلومات:**
» `مشغل` / `الان` / `np` — إيه اللي شغال دلوقتي
» `في الكول` / `كول` / `incall` — مين في الكول
» `قايمة` / `queue` — قايمة الأغاني
» `مده التشغيل` — وقت التشغيل الحالي
» `ايدي` / `id` — عرض الـ ID

**بحث وتحميل:**
» `بحث` / `search` + اسم الأغنية
» `يوت` + اسم — بحث على يوتيوب
» `تحميل` / `song` + اسم — ملف صوتي
» `تحميل فيديو` / `vsong` + اسم — ملف فيديو

**عام:**
» `بينج` / `ping` — سرعة البوت
» `uptime` — مدة تشغيل البوت"""

ADMINS_TEXT = """**🛡️ أوامر المشرفين**

**التحكم في التشغيل:**
» `تخطي` / `skip` — تخطي الأغنية الحالية
» `انهاء` / `اسكت` / `stop` — إيقاف التشغيل
» `ايقاف` / `pause` — إيقاف مؤقت
» `كمل` / `resume` — استكمال التشغيل
» `تحكم` / `صوت` + رقم — مستوى الصوت (1-200)
» `ميوت` / `mute` — كتم صوت البوت
» `فك ميوت` / `unmute` — رفع الكتم

**إدارة الأعضاء:**
» `كتم` / `كتم مستخدم` — رد لكتم عضو
» `فك كتم` / `رفع كتم` — رد لفك الكتم

**القفل والفتح:**
» `قفل` + [صور / روابط / توجيه / دردشة / الكل]
» `فتح` + [صور / روابط / توجيه / دردشة / الكل]

**متنوع:**
» `تحديث` / `update` — تحديث البوت
» `ريستارت` / `restart` — إعادة تشغيل
» `سيرفر` / `sysinfo` — معلومات السيرفر
» `اعاده` / `تحديث الادمن` — تحديث قائمة المشرفين"""

OWNER_TEXT = """**👑 أوامر المالك**

**إدارة المشرفين:**
» `رفع` / `رفع مشرف` / `promote` + رد أو معرف
» `رفع بوت` / `botadmin` + رد أو معرف
» `شيل بوت ادمن` / `rmbotadmin` + رد أو معرف
» `قايمة الادمنز` — عرض قائمة المديرين
» `حد الحظر` / `setbanlimit` + رقم

**الحساب المساعد:**
» `userbotjoin` — انضمام الحساب المساعد
» `userbotleave` — مغادرة الحساب المساعد"""

DEV_TEXT = """**⚙️ أوامر المطور**

**تنفيذ أوامر:**
» `eval` + كود — تنفيذ كود Python
» `sh` + أمر — تنفيذ أمر Shell

**إدارة البوت:**
» `اذاعه` / `broadcast` + رسالة أو رد — إرسال لكل الجروبات
» `ذت` / `اذع` — إذاعة مع تثبيت
» `leaveall` — مغادرة كل الجروبات
» `leavebot` / `مغادره البوت` + ID — مغادرة جروب

**تنظيف السيرفر:**
» `rmd` / `clear` — حذف الملفات المحملة
» `rmw` / `clean` — حذف ملفات raw
» `cleanup` — تنظيف شامل"""

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


def back_keyboard(user_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"cmds_back_{user_id}")],
        [InlineKeyboardButton("✖ إغلاق", callback_data="cmds_close")],
    ])


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


@Client.on_callback_query(filters.regex("^cmds_members$"))
async def cmds_members(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    try:
        await query.edit_message_caption(MEMBERS_TEXT, reply_markup=back_keyboard(user_id))
    except Exception:
        await query.edit_message_text(MEMBERS_TEXT, reply_markup=back_keyboard(user_id))
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_admins$"))
async def cmds_admins_cb(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    try:
        await query.edit_message_caption(ADMINS_TEXT, reply_markup=back_keyboard(user_id))
    except Exception:
        await query.edit_message_text(ADMINS_TEXT, reply_markup=back_keyboard(user_id))
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_owner$"))
async def cmds_owner_cb(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    try:
        await query.edit_message_caption(OWNER_TEXT, reply_markup=back_keyboard(user_id))
    except Exception:
        await query.edit_message_text(OWNER_TEXT, reply_markup=back_keyboard(user_id))
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_dev$"))
async def cmds_dev_cb(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in SUDO_USERS:
        await query.answer("❌ هذا القسم للمطور فقط", show_alert=True)
        return
    try:
        await query.edit_message_caption(DEV_TEXT, reply_markup=back_keyboard(user_id))
    except Exception:
        await query.edit_message_text(DEV_TEXT, reply_markup=back_keyboard(user_id))
    await query.answer()


@Client.on_callback_query(filters.regex(r"^cmds_back_(\d+)$"))
async def cmds_back(c: Client, query: CallbackQuery):
    user_id = query.from_user.id
    try:
        await query.edit_message_caption(MAIN_CAPTION, reply_markup=main_keyboard(user_id))
    except Exception:
        await query.edit_message_text(MAIN_CAPTION, reply_markup=main_keyboard(user_id))
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_close$"))
async def cmds_close(c: Client, query: CallbackQuery):
    await query.message.delete()
    await query.answer()
