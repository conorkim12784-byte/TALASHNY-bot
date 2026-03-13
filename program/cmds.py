# cmds.py — أمر الأوامر مع أزرار تنقل

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from driver.filters import command, command2, other_filters

GIF_URL = "https://i.postimg.cc/wxV3PspQ/1756574872401.gif"

# ═══════════════════════════════════════
# نصوص الأوامر
# ═══════════════════════════════════════
MEMBERS_TEXT = """🎵 **أوامر الأعضاء**

**تشغيل موسيقى:**
» `تشغيل` + اسم الأغنية أو رابط
» `شغل` + اسم الأغنية

**تشغيل فيديو:**
» `تشغيل فيديو` + اسم أو رابط
» `شغل فيديو` + اسم أو رابط

**معلومات:**
» `مشغل` — شوف إيه اللي شغال دلوقتي
» `في الكول` — شوف مين في الدردشة الصوتية
» `قايمة التشغيل` — قايمة الأغاني

**بحث وتحميل:**
» `بحث` + اسم الأغنية
» `بحث يوتيوب` + كلمة البحث
» `تحميل` + اسم الأغنية
» `تحميل فيديو` + اسم الفيديو"""

ADMINS_TEXT = """👮 **أوامر المشرفين**

**التحكم في التشغيل:**
» `تخطي` — تخطي الأغنية الحالية
» `انهاء` — إيقاف التشغيل نهائياً
» `اسكت` — كتم الصوت
» `ايقاف` — إيقاف مؤقت
» `كمل` — استكمال التشغيل
» `تحكم` + رقم — التحكم في مستوى الصوت

**كتم الأعضاء:**
» `ميوت` — كتم مستخدم (رد على رسالته)
» `فك ميوت` — فك الكتم"""

BOT_ADMIN_TEXT = """⚙️ **أوامر بوت الادمن**

**القفل والفتح:**
» `قفل صور` / `فتح صور`
» `قفل روابط` / `فتح روابط`
» `قفل توجيه` / `فتح توجيه`
» `قفل دردشة` / `فتح دردشة`
» `قفل الكل` / `فتح الكل`

**إدارة بوت الادمنز:**
» `رفع بوت` + معرف أو رد — رفع بوت ادمن
» `شيل بوت ادمن` + معرف أو رد — نزول بوت ادمن
» `قايمة الادمنز` — عرض البوت ادمنز

**إدارة المشرفين:**
» `رفع` + معرف أو رد — رفع مشرف جروب
» `حد الحظر` + رقم — تغيير حد الحظر التلقائي"""


def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 أوامر الأعضاء", callback_data="cmds_members"),
            InlineKeyboardButton("👮 أوامر المشرفين", callback_data="cmds_admins"),
        ],
        [
            InlineKeyboardButton("⚙️ بوت الادمن", callback_data="cmds_botadmin"),
        ],
        [InlineKeyboardButton("🗑 اغلاق", callback_data="cmds_close")],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ رجوع", callback_data="cmds_main")],
        [InlineKeyboardButton("🗑 اغلاق", callback_data="cmds_close")],
    ])


# ═══════════════════════════════════════
# أمر الأوامر
# ═══════════════════════════════════════
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


# ═══════════════════════════════════════
# callbacks التنقل
# ═══════════════════════════════════════
@Client.on_callback_query(filters.regex("^cmds_main$"))
async def cmds_back_main(c: Client, query: CallbackQuery):
    await query.edit_message_caption(
        "**اختار تصنيف الأوامر اللي عايزه 👇**",
        reply_markup=main_keyboard()
    )
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_members$"))
async def cmds_members(c: Client, query: CallbackQuery):
    await query.edit_message_caption(
        MEMBERS_TEXT,
        reply_markup=back_keyboard()
    )
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_admins$"))
async def cmds_admins(c: Client, query: CallbackQuery):
    await query.edit_message_caption(
        ADMINS_TEXT,
        reply_markup=back_keyboard()
    )
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_botadmin$"))
async def cmds_botadmin(c: Client, query: CallbackQuery):
    await query.edit_message_caption(
        BOT_ADMIN_TEXT,
        reply_markup=back_keyboard()
    )
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_close$"))
async def cmds_close(c: Client, query: CallbackQuery):
    await query.message.delete()
    await query.answer()
