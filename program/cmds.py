# cmds.py — أمر الأوامر مع أزرار زرقاء

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from driver.filters import command, command2, other_filters

GIF_URL = "https://i.postimg.cc/wxV3PspQ/1756574872401.gif"

MEMBERS_TEXT = """🎵 **أوامر الأعضاء**

**تشغيل:**
» `تشغيل` + اسم أو رابط
» `تشغيل فيديو` + اسم أو رابط

**معلومات:**
» `مشغل` — إيه اللي شغال دلوقتي
» `في الكول` — مين في الدردشة الصوتية
» `قايمة التشغيل` — قايمة الأغاني

**بحث وتحميل:**
» `بحث` + اسم الأغنية
» `بحث يوتيوب` + كلمة البحث
» `تحميل` + اسم الأغنية
» `تحميل فيديو` + اسم الفيديو"""

ADMINS_TEXT = """👮 **أوامر المشرفين**

**التحكم في التشغيل:**
» `تخطي` — تخطي الأغنية
» `انهاء` — إيقاف نهائي
» `اسكت` — كتم الصوت
» `ايقاف` — إيقاف مؤقت
» `كمل` — استكمال
» `تحكم` + رقم — مستوى الصوت

**كتم الأعضاء:**
» `ميوت` — كتم (رد على رسالته)
» `فك ميوت` — فك الكتم"""

BOT_ADMIN_TEXT = """⚙️ **أوامر بوت الادمن**

**القفل والفتح:**
» `قفل صور` / `فتح صور`
» `قفل روابط` / `فتح روابط`
» `قفل توجيه` / `فتح توجيه`
» `قفل دردشة` / `فتح دردشة`
» `قفل الكل` / `فتح الكل`

**إدارة بوت الادمنز:**
» `رفع بوت` + معرف أو رد
» `شيل بوت ادمن` + معرف أو رد
» `قايمة الادمنز`

**إدارة المشرفين:**
» `رفع` + معرف أو رد
» `حد الحظر` + رقم"""


def main_rows():
    return [
        [
            {"text": "🎵 أوامر الأعضاء", "callback_data": "cmds_members", "style": "primary"},
            {"text": "👮 أوامر المشرفين", "callback_data": "cmds_admins", "style": "primary"},
        ],
        [
            {"text": "⚙️ بوت الادمن", "callback_data": "cmds_botadmin", "style": "primary"},
        ],
        [{"text": "🗑 اغلاق", "callback_data": "cmds_close", "style": "primary"}],
    ]


def back_rows():
    return [
        [{"text": "◀️ رجوع", "callback_data": "cmds_main", "style": "primary"}],
        [{"text": "🗑 اغلاق", "callback_data": "cmds_close", "style": "primary"}],
    ]


# تخزين message_id لكل chat
_msg_ids: dict = {}


@Client.on_message((command(["commands", "cmds"]) | command2(["الاوامر", "اوامر"])) & other_filters)
async def show_commands(c: Client, m: Message):
    await m.delete()
    result = await send_blue_animation(
        m.chat.id,
        GIF_URL,
        "**اختار تصنيف الأوامر 👇**",
        main_rows()
    )
    if result and result.get("ok"):
        _msg_ids[m.chat.id] = result["result"]["message_id"]


@Client.on_callback_query(filters.regex("^cmds_main$"))
async def cmds_back_main(c: Client, query: CallbackQuery):
    await edit_blue_caption(
        query.message.chat.id,
        query.message.id,
        "**اختار تصنيف الأوامر 👇**",
        main_rows()
    )
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_members$"))
async def cmds_members(c: Client, query: CallbackQuery):
    await edit_blue_caption(query.message.chat.id, query.message.id, MEMBERS_TEXT, back_rows())
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_admins$"))
async def cmds_admins_cb(c: Client, query: CallbackQuery):
    await edit_blue_caption(query.message.chat.id, query.message.id, ADMINS_TEXT, back_rows())
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_botadmin$"))
async def cmds_botadmin_cb(c: Client, query: CallbackQuery):
    await edit_blue_caption(query.message.chat.id, query.message.id, BOT_ADMIN_TEXT, back_rows())
    await query.answer()


@Client.on_callback_query(filters.regex("^cmds_close$"))
async def cmds_close(c: Client, query: CallbackQuery):
    await query.message.delete()
    await query.answer()
