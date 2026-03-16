# cmds.py — أمر الأوامر مع أزرار تنقل

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from driver.filters import command, command2, other_filters

GIF_URL = "https://i.postimg.cc/wxV3PspQ/1756574872401.gif"

MEMBERS_TEXT = """ **أوامر الأعضاء**

**تشغيل موسيقى:**
» `شغل` / `تشغيل` + اسم الأغنية أو رابط
» `play` / `mplay` + اسم الأغنية

**تشغيل فيديو:**
» `شغل فيديو` / `تشغيل فيديو` + اسم أو رابط
» `vplay` + اسم أو رابط

**معلومات:**
» `مشغل` / `الان` / `مين مشغل` — إيه اللي شغال
» `في الكول` / `كول` / `مين في الكول` — مين في الكول
» `قايمة التشغيل` / `queue` — قايمة الأغاني
» `ايدي` — عرض الـ ID

**بحث وتحميل:**
» `بحث` / `search` + اسم الأغنية
» `تحميل` / `song` + اسم الأغنية — ملف صوتي
» `تحميل فيديو` / `vsong` + اسم — ملف فيديو
» `كلمات` / `lyric` + اسم الأغنية"""

ADMINS_TEXT = """ **أوامر المشرفين**

**التحكم في التشغيل:**
» `تخطي` / `skip` — تخطي الأغنية الحالية
» `انهاء` / `stop` — إيقاف التشغيل نهائياً
» `ايقاف` / `pause` — إيقاف مؤقت
» `كمل` / `resume` — استكمال التشغيل
» `تحكم` / `volume` + رقم — مستوى الصوت (1-200)

**كتم البث الصوتي:**
» `ميوت` / `mute` — كتم صوت البوت في الكول
» `فك ميوت` / `unmute` — فك كتم البوت

**كتم الأعضاء:**
» `كتم` / `كتم مستخدم` — رد على رسالة لكتم عضو
» `فك كتم` / `رفع كتم` — رد على رسالة لفك الكتم"""

BOT_ADMIN_TEXT = """ **أوامر المدريين**

**القفل والفتح:**
» `قفل صور` / `فتح صور`
» `قفل روابط` / `فتح روابط`
» `قفل توجيه` / `فتح توجيه`
» `قفل دردشة` / `فتح دردشة`
» `قفل الكل` / `فتح الكل`

**إدارة المدريينز:**
» `رفع مدير` / `رفع بوت` + معرف أو رد
» `شيل بوت ادمن` + معرف أو رد
» `قايمة الادمنز` — عرض قايمة المديرين

**إدارة المشرفين:**
» `رفع مشرف` / `رفع` + معرف أو رد
» `حد الحظر` + رقم — تغيير حد الحظر التلقائي"""


def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("  الأعضاء", callback_data="cmds_members"),
            InlineKeyboardButton("  المشرفين", callback_data="cmds_admins"),
        ],
        [InlineKeyboardButton(" المدريين", callback_data="cmds_botadmin")],
        [InlineKeyboardButton(" اغلاق", callback_data="cmds_close")],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(" رجوع", callback_data="cmds_main")],
        [InlineKeyboardButton(" اغلاق", callback_data="cmds_close")],
    ])


@Client.on_message((command(["commands", "cmds"]) | command2(["الاوامر", "اوامر"])) & other_filters)
async def show_commands(c: Client, m: Message):
    await m.delete()
    try:
        await c.send_animation(
            m.chat.id,
            animation=GIF_URL,
            caption="**اختار تصنيف الأوامر اللي عايزه 👇**",
            reply_markup=main_keyboard()
        )
    except Exception:
        await m.reply(
            "**اختار تصنيف الأوامر اللي عايزه 👇**",
            reply_markup=main_keyboard()
        )


@Client.on_callback_query(filters.regex("^cmds_main$"))
async def cmds_back_main(c: Client, query: CallbackQuery):
    try:
        await query.edit_message_caption(
            "**╭────⌁TALASHNY⌁────⟤\n│╭───────────⟢\n╞╡          Command List \n╞╡ \n╞╡ Select A Button To Learn More \n│╰────────────╮\n│╭────────────╯\n╞╡   Enjoy A Unique Experience \n│╰───────────⟢\n╰────⌁TALASHNY⌁────⟤**",
            reply_markup=main_keyboard()
        )
    except Exception:
        await query.edit_message_text(
            "**╭────⌁TALASHNY⌁────⟤\n│╭───────────⟢\n╞╡          Command List \n╞╡ \n╞╡ Select A Button To Learn More \n│╰────────────╮\n│╭────────────╯\n╞╡   Enjoy A Unique Experience \n│╰───────────⟢\n╰────⌁TALASHNY⌁────⟤**",
            reply_markup=main_keyboard()
        )
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_members$"))
async def cmds_members(c: Client, query: CallbackQuery):
    try:
        await query.edit_message_caption(MEMBERS_TEXT, reply_markup=back_keyboard())
    except Exception:
        await query.edit_message_text(MEMBERS_TEXT, reply_markup=back_keyboard())
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_admins$"))
async def cmds_admins_cb(c: Client, query: CallbackQuery):
    try:
        await query.edit_message_caption(ADMINS_TEXT, reply_markup=back_keyboard())
    except Exception:
        await query.edit_message_text(ADMINS_TEXT, reply_markup=back_keyboard())
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_botadmin$"))
async def cmds_botadmin_cb(c: Client, query: CallbackQuery):
    try:
        await query.edit_message_caption(BOT_ADMIN_TEXT, reply_markup=back_keyboard())
    except Exception:
        await query.edit_message_text(BOT_ADMIN_TEXT, reply_markup=back_keyboard())
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_close$"))
async def cmds_close(c: Client, query: CallbackQuery):
    await query.message.delete()
    await query.answer()
