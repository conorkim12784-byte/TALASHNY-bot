# cmds.py — قائمة الأوامر الموحدة (نسخة معدّلة بألوان أزرار + ترتيب حسب الصلاحية)

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from driver.filters import command, command2, other_filters
from config import BOT_NAME, BOT_PHOTO, UPDATES_CHANNEL, GROUP_SUPPORT, SUDO_USERS
from program.utils.colored_buttons import BTN

GIF_URL = "https://i.postimg.cc/wxV3PspQ/1756574872401.gif"

# ═══════════════════════════════════════
# الكابشن الرئيسي (الصيغة المطلوبة)
# ═══════════════════════════════════════
MAIN_CAPTION = """**╭────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁────⟤
│╭───────────⟢
╞𝗧-       قائمة الأوامر
╞╡
╞𝗧-  اختر القسم اللي تريده
│╰───────────⟢
╰────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁────⟤**"""


# ═══════════════════════════════════════
# الكيبوردات (الترتيب: أعضاء/ألعاب → مشرفين → مالك → مطور)
#
# ألوان الأزرار حسب وظيفتها:
#   - الأقسام المحايدة (أعضاء/مشرفين/مالك)        → DEFAULT
#   - الأقسام الإيجابية (الألعاب — للترفيه)        → success (أخضر)
#   - الأقسام الإدارية الحساسة (المطور)            → danger  (أحمر)
#   - أزرار اللغة (info/معلومات)                   → primary (أزرق)
#   - زر الرجوع                                     → primary (أزرق)
#   - زر الإغلاق                                    → danger  (أحمر)
# ═══════════════════════════════════════
def main_keyboard(user_id: int):
    rows = [
        # الصف الأول: المستوى الأقل صلاحية (الأعضاء + الألعاب الترفيهية)
        [
            BTN("الأعضاء", "cmds_members"),
            BTN("الألعاب", "cmds_games", "success"),
        ],
        # الصف الثاني: المشرفين
        [
            BTN("المشرفين", "cmds_admins"),
        ],
        # الصف الثالث: المالك
        [
            BTN("المالك", "cmds_owner"),
        ],
    ]
    if user_id in SUDO_USERS:
        # المطور — أعلى صلاحية، أحمر
        rows.append([BTN("المطور", "cmds_dev", "danger")])
    rows.append([BTN("إغلاق", "cmds_close", "danger")])
    return InlineKeyboardMarkup(rows)


def section_keyboard(user_id: int, section: str):
    """كيبورد داخل كل قسم — عربي / انجليزي + رجوع"""
    return InlineKeyboardMarkup([
        [
            BTN("عربي", f"{section}_ar", "primary"),
            BTN("English", f"{section}_en", "primary"),
        ],
        [BTN("رجوع", f"cmds_back_{user_id}", "primary")],
        [BTN("إغلاق", "cmds_close", "danger")],
    ])


def back_keyboard(user_id: int, section: str):
    """كيبورد في صفحة الأوامر — زرار رجوع للقسم"""
    return InlineKeyboardMarkup([
        [BTN("رجوع", f"cmds_{section}", "primary")],
        [BTN("إغلاق", "cmds_close", "danger")],
    ])


# ═══════════════════════════════════════
# نصوص الأوامر (بدون تغيير)
# ═══════════════════════════════════════
MEMBERS_AR = """**أوامر الأعضاء — عربي**

**▸ تشغيل موسيقى:**
`تشغيل` — تشغيل أغنية باسمها أو رابط
`شغل` — نفس تشغيل

**▸ تشغيل فيديو:**
`فيد` — تشغيل فيديو
`فيديو` — نفس فيد
`ستريم` — تشغيل بث مباشر برابط

**▸ بحث وتحميل:**
`بحث` — بحث عن أغنية
`يوت` — بحث على يوتيوب
`تحميل` — تحميل أغنية كملف صوتي
`تحميل فيديو` — تحميل فيديو كملف

**▸ معلومات:**
`مين مشغل` — الأغنية الشغالة دلوقتي
`مين في الكول` — يعرض مين في الكول
`مده التشغيل` — وقت التشغيل الحالي
`ايدي` — عرض الـ ID

**▸ القائمة:**
`قائمه` — قائمة الأغاني في الانتظار

**▸ ردود:**
`بوت` — البوت يرد عليك برد عشوائي

**▸ عام:**
`بينج` — سرعة البوت
`المالك` — عرض بيانات صاحب البوت/المجموعة"""

MEMBERS_EN = """**Members Commands — English**

**▸ Play Music:**
`play` — play a song by name or link
`mplay` — same as play

**▸ Play Video:**
`vplay` — play a video
`vstream` — stream a direct link

**▸ Search & Download:**
`search` — search for a song
`song` — download song as audio
`vsong` / `video` — download video as file

**▸ Info:**
`np` / `nowplaying` — currently playing
`incall` — who is in the call
`uptime` — bot uptime
`id` — show user/chat ID

**▸ Queue:**
`queue` / `playlist` — songs queue

**▸ General:**
`ping` — bot speed"""

ADMINS_AR = """**أوامر المشرفين — عربي**

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
`فك كتم` — رد على رسالة لفك الكتم

**▸ القفل والفتح:**
`قفل` — قفل الجروب (صور/روابط/دردشة/الكل)
`فتح` — فتح الجروب"""

ADMINS_EN = """**Admins Commands — English**

**▸ Playback Control:**
`skip` — skip current song
`stop` — stop and leave call
`pause` — pause playback
`resume` — resume playback
`mute` — mute the bot
`unmute` — unmute the bot

**▸ Locks:**
`lock` / `unlock` — group locks"""

OWNER_AR = """**أوامر المالك — عربي**

**▸ إدارة المشرفين والمديرين:**
`رفع مشرف` — رفع عضو مشرف للجروب (صلاحيات الجروب)
`رفع مدير` — رفع عضو مدير في البوت (صلاحيات البوت)
`تنزيل مدير` — تنزيل المدير من البوت
`قائمة المديرين` — عرض قائمة المديرين
`تحديث` / `اعاده` — تحديث قائمة المشرفين والمالك
`تحديث الادمن` — نفس اعاده

**▸ إدارة المالك:**
`المالك` — عرض بيانات المالك الحالي
`تغيير يوزر المالك` — تغيير المالك الظاهر للبوت
`تحديث المالك` — إرجاع المالك للمالك الرسمي

**▸ الاشتراك الإجباري (لأصحاب البوت):**
`اشتراك اجباري` — لوحة التحكم بأزرار (تفعيل/تعطيل/ضبط القناة)
`ضبط قناة الاشتراك` — تحديد القناة المطلوب الاشتراك فيها

**▸ نظام الهمس (للمشرفين/المالك):**
`الهمس` — لوحة التحكم بأزرار
`تفعيل الهمس` / `تعطيل الهمس`
الاستخدام: `@BotUsername @user رسالتك`

**▸ متنوع:**
`تحديث_البوت` — تحديث البوت
`ريستارت` — إعادة تشغيل البوت
`سيرفر` — معلومات السيرفر
`حد الحظر` — تحديد حد الحظر التلقائي"""

OWNER_EN = """**Owner Commands — English**

**▸ Admin Management:**
`promote` — promote a member to group admin
`botadmin` — promote a member to bot manager
`rmbotadmin` — demote a bot manager
`botadmins` — list bot managers
`setbanlimit` — set auto-ban limit

**▸ Owner Management:**
`owner` — show current owner info
`change_owner` — change displayed owner
`reset_owner` — reset displayed owner to the real one

**▸ Force Subscribe (sudo only):**
`fsub` / `force_sub` — control panel (toggle / set channel)

**▸ Whisper:**
`whisper` — control panel (admins+)
`enable_whisper` / `disable_whisper`
Usage: `@BotUsername @user your secret message`

**▸ Misc:**
`update` — update the bot
`restart` — restart the bot
`sysinfo` — server information
`uptime` — bot uptime"""

DEV_AR = """**أوامر المطور — عربي**

**▸ تنفيذ:**
`eval` — تنفيذ كود Python
`sh` — تنفيذ أمر Shell

**▸ إدارة البوت:**
`اذاعه` / `اذاعة` — إذاعة نص أو رد على رسالة لكل الجروبات
`اذاعه فوروورد` — إذاعة بالفوروارد
`ذت` / `اذت` — إذاعة مع تثبيت
`leaveall` — مغادرة كل الجروبات
`مغادره البوت` — مغادرة جروب معين

**▸ تنظيف السيرفر:**
`rmd` / `clear` — حذف الملفات المحملة
`rmw` / `clean` — حذف ملفات raw
`cleanup` — تنظيف شامل"""

DEV_EN = """**Developer Commands — English**

**▸ Execute:**
`eval` — execute Python code
`sh` — execute Shell command

**▸ Bot Management:**
`broadcast` / `gcast` — broadcast to all groups
`pcast` / `pgcast` — broadcast + pin
`leaveall` — leave all groups
`leavebot` — leave a specific group

**▸ Cleanup:**
`rmd` / `clear` — delete downloaded files
`rmw` / `clean` — delete raw files
`cleanup` — full cleanup"""

GAMES_AR = """**أوامر الألعاب**

**▸ نظام الزواج:**
`زوجني` (بالرد أو @user) — تطلب الزواج، الطرف التاني يوافق أو يرفض بزر
`زوجني` (لوحده من غير معرف أو رد) — يختار شخص عشوائي ويزوّجك له فورًا
`زوجي` — يعرض شريك حياتك في الجروب
`طلاق` — تطلق شريكك الحالي

**▸ لعبة XO (إكس أو):**
`xo` (بالرد أو @user) — تبدأ لعبة XO ضد عضو محدد
`xo` (لوحده) — تبعت طلب لعبة وأول واحد يضغط «انضمام» يبقى خصمك
`اكس` — نفس الأمر

**▸ لعبة كات:**
`كت` — سؤال طريف بأسلوب القطط (الاسم الجديد للأمر)

**▸ لعبة صراحة:**
`صراحة` — سؤال صراحة عشوائي
`صراحة معاك` (بالرد أو لنفسك) — حقيقة عنك بأسلوب لطيف

**▸ التاك (منشن الأعضاء):**
`تاك [عدد]` — منشن لعدد من الأعضاء (مثال: `تاك 30`)
`تاك الكل` — منشن لكل أعضاء الجروب
`تاك [عدد] [رسالة]` — تاك مع رسالة (مثال: `تاك 20 الجلسة دلوقتي`)
`تفعيل التاك` / `تعطيل التاك` — التحكم في الأمر

_أمر التاك مخصّص لـ: المالك الرسمي / أصحاب البوت / مالك الجروب / مدير البوت بصلاحية «التاك»_

**ملاحظات:**
• كل لعبة بتشتغل مع أي عضو في الجروب
• الزواج محفوظ لكل جروب على حدة"""


# ═══════════════════════════════════════
# الأوامر الرئيسية
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


# ═══════════════════════════════════════
# دالة مشتركة لتعديل الرسالة (caption أو text)
# ═══════════════════════════════════════
async def _safe_edit(query: CallbackQuery, text: str, kb: InlineKeyboardMarkup):
    try:
        await query.edit_message_caption(text, reply_markup=kb)
    except Exception:
        try:
            await query.edit_message_text(text, reply_markup=kb)
        except Exception:
            pass


# ── قسم الأعضاء ──
@Client.on_callback_query(filters.regex("^cmds_members$"))
async def cmds_members(c: Client, query: CallbackQuery):
    kb = section_keyboard(query.from_user.id, "members")
    await _safe_edit(query, "**أوامر الأعضاء**\n\nاختار اللغة:", kb)
    await query.answer()

@Client.on_callback_query(filters.regex("^members_ar$"))
async def members_ar(c: Client, query: CallbackQuery):
    await _safe_edit(query, MEMBERS_AR, back_keyboard(query.from_user.id, "members"))
    await query.answer()

@Client.on_callback_query(filters.regex("^members_en$"))
async def members_en(c: Client, query: CallbackQuery):
    await _safe_edit(query, MEMBERS_EN, back_keyboard(query.from_user.id, "members"))
    await query.answer()


# ── قسم المشرفين ──
@Client.on_callback_query(filters.regex("^cmds_admins$"))
async def cmds_admins_cb(c: Client, query: CallbackQuery):
    await _safe_edit(query, "**أوامر المشرفين**\n\nاختار اللغة:", section_keyboard(query.from_user.id, "admins"))
    await query.answer()

@Client.on_callback_query(filters.regex("^admins_ar$"))
async def admins_ar(c: Client, query: CallbackQuery):
    await _safe_edit(query, ADMINS_AR, back_keyboard(query.from_user.id, "admins"))
    await query.answer()

@Client.on_callback_query(filters.regex("^admins_en$"))
async def admins_en(c: Client, query: CallbackQuery):
    await _safe_edit(query, ADMINS_EN, back_keyboard(query.from_user.id, "admins"))
    await query.answer()


# ── قسم المالك ──
@Client.on_callback_query(filters.regex("^cmds_owner$"))
async def cmds_owner_cb(c: Client, query: CallbackQuery):
    await _safe_edit(query, "**أوامر المالك**\n\nاختار اللغة:", section_keyboard(query.from_user.id, "owner"))
    await query.answer()

@Client.on_callback_query(filters.regex("^owner_ar$"))
async def owner_ar(c: Client, query: CallbackQuery):
    await _safe_edit(query, OWNER_AR, back_keyboard(query.from_user.id, "owner"))
    await query.answer()

@Client.on_callback_query(filters.regex("^owner_en$"))
async def owner_en(c: Client, query: CallbackQuery):
    await _safe_edit(query, OWNER_EN, back_keyboard(query.from_user.id, "owner"))
    await query.answer()


# ── قسم المطور ──
@Client.on_callback_query(filters.regex("^cmds_dev$"))
async def cmds_dev_cb(c: Client, query: CallbackQuery):
    if query.from_user.id not in SUDO_USERS:
        await query.answer("هذا القسم للمطور فقط", show_alert=True)
        return
    await _safe_edit(query, "**أوامر المطور**\n\nاختار اللغة:", section_keyboard(query.from_user.id, "dev"))
    await query.answer()

@Client.on_callback_query(filters.regex("^dev_ar$"))
async def dev_ar(c: Client, query: CallbackQuery):
    if query.from_user.id not in SUDO_USERS:
        await query.answer("للمطور فقط", show_alert=True)
        return
    await _safe_edit(query, DEV_AR, back_keyboard(query.from_user.id, "dev"))
    await query.answer()

@Client.on_callback_query(filters.regex("^dev_en$"))
async def dev_en(c: Client, query: CallbackQuery):
    if query.from_user.id not in SUDO_USERS:
        await query.answer("للمطور فقط", show_alert=True)
        return
    await _safe_edit(query, DEV_EN, back_keyboard(query.from_user.id, "dev"))
    await query.answer()


# ── قسم الألعاب ──
@Client.on_callback_query(filters.regex("^cmds_games$"))
async def cmds_games_cb(c: Client, query: CallbackQuery):
    kb = InlineKeyboardMarkup([
        [BTN("رجوع", f"cmds_back_{query.from_user.id}", "primary")],
        [BTN("إغلاق", "cmds_close", "danger")],
    ])
    await _safe_edit(query, GAMES_AR, kb)
    await query.answer()


# ── رجوع للرئيسية ──
@Client.on_callback_query(filters.regex(r"^cmds_back_(\d+)$"))
async def cmds_back(c: Client, query: CallbackQuery):
    await _safe_edit(query, MAIN_CAPTION, main_keyboard(query.from_user.id))
    await query.answer()


# ── إغلاق ──
@Client.on_callback_query(filters.regex("^cmds_close$"))
async def cmds_close(c: Client, query: CallbackQuery):
    try:
        await query.message.delete()
    except Exception:
        pass
    await query.answer()
