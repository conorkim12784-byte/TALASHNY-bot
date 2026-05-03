# cmds.py — قائمة الأوامر الموحدة (نسخة معدّلة)
# المستجدات:
#   • قسم «حماية الجروب» مستقل (أمر القفل والفتح والكتم وفك الكتم)
#   • كل رتبة ليها زرارها (الأعضاء / المشرفين / حماية الجروب / المالك / المطور / الألعاب)
#   • قسم الألعاب محدّث (تفكيك / تجميع / قرعة / توب نقاط + تفعيل وتعطيل الألعاب)

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from driver.filters import command, command2, other_filters
from config import SUDO_USERS

GIF_URL = "https://i.postimg.cc/wxV3PspQ/1756574872401.gif"

# ═══════════════════════════════════════
# الكابشن الرئيسي
# ═══════════════════════════════════════
MAIN_CAPTION = """**╭────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁────⟤
│╭───────────⟢
╞𝗧-       قائمة الأوامر
╞╡
╞𝗧-  اختر القسم اللي تريده
│╰───────────⟢
╰────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁────⟤**"""


def main_keyboard(user_id: int):
    """كل رتبة ليها زر مستقل."""
    rows = [
        [InlineKeyboardButton("الأعضاء", callback_data="cmds_members")],
        [InlineKeyboardButton("المشرفين", callback_data="cmds_admins")],
        [InlineKeyboardButton("حماية الجروب", callback_data="cmds_protect")],
        [InlineKeyboardButton("المالك", callback_data="cmds_owner")],
        [InlineKeyboardButton("الألعاب", callback_data="cmds_games")],
    ]
    if user_id in SUDO_USERS:
        rows.append([InlineKeyboardButton("المطور", callback_data="cmds_dev")])
    rows.append([InlineKeyboardButton("إغلاق", callback_data="cmds_close")])
    return InlineKeyboardMarkup(rows)


def section_keyboard(user_id: int, section: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("عربي", callback_data=f"{section}_ar"),
            InlineKeyboardButton("English", callback_data=f"{section}_en"),
        ],
        [InlineKeyboardButton("رجوع", callback_data=f"cmds_back_{user_id}")],
        [InlineKeyboardButton("إغلاق", callback_data="cmds_close")],
    ])


def back_keyboard(user_id: int, section: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("رجوع", callback_data=f"cmds_{section}")],
        [InlineKeyboardButton("إغلاق", callback_data="cmds_close")],
    ])


# ═══════════════════════════════════════
# نصوص الأوامر
# ═══════════════════════════════════════
MEMBERS_AR = """**أوامر الأعضاء — عربي**

**▸ تشغيل موسيقى:**
`تشغيل` — تشغيل أغنية باسمها أو رابط
`شغل` — نفس تشغيل

**▸ تشغيل فيديو:**
`فيد` / `فيديو` — تشغيل فيديو
`ستريم` — بث مباشر برابط

**▸ بحث وتحميل:**
`بحث` — بحث عن أغنية
`يوت` — بحث على يوتيوب
`تحميل` — تحميل أغنية كملف صوتي
`تحميل فيديو` — تحميل فيديو كملف

**▸ معلومات:**
`مين مشغل` — الأغنية الشغالة
`مين في الكول` — الموجودين في الكول
`مده التشغيل` — وقت التشغيل
`ايدي` — عرض الـ ID

**▸ القائمة:**
`قائمه` — قائمة الانتظار

**▸ ردود:**
`بوت` — رد عشوائي

**▸ عام:**
`بينج` — سرعة البوت
`المالك` — بيانات صاحب البوت"""

MEMBERS_EN = """**Members Commands — English**

`play` / `mplay` — play a song
`vplay` / `vstream` — play video / stream
`search` / `song` / `vsong` — search & download
`np` / `incall` / `uptime` / `id`
`queue` / `playlist` — songs queue
`ping` — bot speed"""

ADMINS_AR = """**أوامر المشرفين — عربي**

**▸ التحكم في التشغيل:**
`تخطي` — تخطي الأغنية
`انهاء` / `اسكت` — إيقاف ومغادرة الكول
`ايقاف` — إيقاف مؤقت
`كمل` — استكمال
`ميوت` / `فك ميوت` — كتم البوت
`تحكم` / `صوت` — مستوى الصوت (1-200)"""

ADMINS_EN = """**Admins Commands — English**

`skip` / `stop`
`pause` / `resume`
`mute` / `unmute`"""

PROTECT_AR = """**أوامر حماية الجروب — عربي**

**▸ القفل والفتح:**
`قفل` — قفل الجروب (صور / روابط / دردشة / توجيه / الكل)
`فتح` — فتح الجروب
مثال: `قفل صور` / `فتح روابط` / `قفل الكل`

**▸ كتم الأعضاء:**
`كتم` — رد على رسالة لكتم العضو
`فك كتم` — رد على رسالة لفك الكتم

**▸ متفرقات حماية:**
`حد الحظر` — تحديد حد الحظر التلقائي

_للمالك / مدير الجروب / مدير البوت بصلاحية «قفل وفتح» أو «كتم وفك كتم»_"""

PROTECT_EN = """**Group Protection — English**

`lock` / `unlock` — lock/unlock group (media/links/chat/forward/all)
`mute` / `unmute` — reply to a message
`setbanlimit` — auto-ban threshold"""

OWNER_AR = """**أوامر المالك — عربي**

**▸ إدارة المشرفين والمديرين:**
`رفع مشرف` — رفع عضو مشرف للجروب
`رفع مدير` — رفع عضو مدير في البوت
`تنزيل مدير` — تنزيل المدير
`قائمة المديرين` — عرض المديرين
`تحديث` / `اعاده` — تحديث قائمة المشرفين

**▸ إدارة المالك:**
`المالك` — بيانات المالك
`تغيير يوزر المالك` / `تحديث المالك`

**▸ الاشتراك الإجباري:**
`اشتراك اجباري` — لوحة التحكم
`ضبط قناة الاشتراك`

**▸ الهمس:**
`الهمس` / `تفعيل الهمس` / `تعطيل الهمس`

**▸ متنوع:**
`تحديث_البوت` / `ريستارت` / `سيرفر`"""

OWNER_EN = """**Owner Commands — English**

`promote` / `botadmin` / `rmbotadmin` / `botadmins`
`owner` / `change_owner` / `reset_owner`
`fsub` / `force_sub`
`whisper` / `enable_whisper` / `disable_whisper`
`update` / `restart` / `sysinfo`"""

DEV_AR = """**أوامر المطور — عربي**

**▸ تنفيذ:**
`eval` — تنفيذ كود Python
`sh` — تنفيذ أمر Shell

**▸ إدارة البوت:**
`اذاعه` / `اذاعه فوروورد` / `ذت`
`leaveall` / `مغادره البوت`

**▸ تنظيف:**
`rmd` / `clear` / `rmw` / `clean` / `cleanup`"""

DEV_EN = """**Developer Commands — English**

`eval` / `sh`
`broadcast` / `gcast` / `pcast` / `pgcast`
`leaveall` / `leavebot`
`rmd` / `clear` / `rmw` / `clean` / `cleanup`"""

GAMES_AR = """**🎮 أوامر الألعاب**

**▸ التحكم في الألعاب (للمشرفين):**
`تفعيل الالعاب` / `تعطيل الالعاب`

**▸ 💍 الزواج (بموافقة الطرف التاني):**
`زوجني` (بالرد أو @user) — عرض زواج، الطرف التاني يوافق أو يرفض بزر
`زوجي` — يعرض شريك حياتك
`طلاق` — تطلق شريكك

**▸ ❌⭕ XO + نقاط:**
`xo` (بالرد أو @user) — لعبة XO ضد عضو محدد
`xo` (لوحده) — أول واحد يضغط «انضمام» يبقى خصمك
🏆 الفوز: +3 نقاط — التعادل: +1 لكل لاعب

**▸ 🐱 كت:**
`كت` — سؤال عام عشوائي

**▸ 🔤 تفكيك (نقاط):**
`تفكيك` — كلمة مبعثرة، رتّبها وكوّن الأصلية
🏆 +5 نقاط لأول إجابة صح

**▸ 🧩 تجميع (نقاط):**
`تجميع` — حروف متفرقة، كوّن منها كلمة
🏆 +5 نقاط لأول إجابة صح

**▸ 🎯 قرعة:**
`قرعة محمد، أحمد، علي` — البوت يختار واحد عشوائي

**▸ 🏆 ترتيب النقاط:**
`توب` / `ترتيب` — توب 10 على كل الجروبات
`نقاطي` — نقاطك الحالية

**▸ 🏷️ التاك (مش لعبة):**
`تاك [عدد]` / `تاك الكل` / `تاك [عدد] [رسالة]`
`تفعيل التاك` / `تعطيل التاك`

_النقاط تراكمية على كل الجروبات — أي حد يكتب «توب» في أي جروب يشوف نفس الترتيب._"""


# ═══════════════════════════════════════
# الأوامر الرئيسية
# ═══════════════════════════════════════
@Client.on_message(
    (command(["commands", "cmds", "help"]) | command2(["الاوامر", "اوامر"])) & other_filters
)
async def show_commands(c: Client, m: Message):
    try:
        await m.delete()
    except Exception:
        pass
    user_id = m.from_user.id
    try:
        await c.send_animation(
            m.chat.id, animation=GIF_URL, caption=MAIN_CAPTION,
            reply_markup=main_keyboard(user_id),
        )
    except Exception:
        await m.reply(MAIN_CAPTION, reply_markup=main_keyboard(user_id))


@Client.on_message(command(["help", "h"]) & filters.private)
async def help_private(c: Client, m: Message):
    user_id = m.from_user.id
    try:
        await m.reply_animation(animation=GIF_URL, caption=MAIN_CAPTION, reply_markup=main_keyboard(user_id))
    except Exception:
        await m.reply(MAIN_CAPTION, reply_markup=main_keyboard(user_id))


# ═══════════════════════════════════════
# تعديل آمن (caption أو text)
# ═══════════════════════════════════════
async def _safe_edit(query: CallbackQuery, text: str, kb: InlineKeyboardMarkup):
    try:
        await query.edit_message_caption(text, reply_markup=kb)
    except Exception:
        try:
            await query.edit_message_text(text, reply_markup=kb)
        except Exception:
            pass


# ── أقسام بزرار عربي/إنجليزي ──
def _make_section(name: str, ar_text: str, en_text: str, sudo_only: bool = False):
    @Client.on_callback_query(filters.regex(f"^cmds_{name}$"))
    async def _open(c, q: CallbackQuery, _name=name, _so=sudo_only):
        if _so and q.from_user.id not in SUDO_USERS:
            return await q.answer("هذا القسم للمطور فقط", show_alert=True)
        await _safe_edit(q, f"**{_name.upper()}**\n\nاختار اللغة:", section_keyboard(q.from_user.id, _name))
        await q.answer()

    @Client.on_callback_query(filters.regex(f"^{name}_ar$"))
    async def _ar(c, q: CallbackQuery, _name=name, _so=sudo_only, _t=ar_text):
        if _so and q.from_user.id not in SUDO_USERS:
            return await q.answer("للمطور فقط", show_alert=True)
        await _safe_edit(q, _t, back_keyboard(q.from_user.id, _name)); await q.answer()

    @Client.on_callback_query(filters.regex(f"^{name}_en$"))
    async def _en(c, q: CallbackQuery, _name=name, _so=sudo_only, _t=en_text):
        if _so and q.from_user.id not in SUDO_USERS:
            return await q.answer("للمطور فقط", show_alert=True)
        await _safe_edit(q, _t, back_keyboard(q.from_user.id, _name)); await q.answer()


_make_section("members", MEMBERS_AR, MEMBERS_EN)
_make_section("admins",  ADMINS_AR,  ADMINS_EN)
_make_section("protect", PROTECT_AR, PROTECT_EN)
_make_section("owner",   OWNER_AR,   OWNER_EN)
_make_section("dev",     DEV_AR,     DEV_EN, sudo_only=True)


# ── قسم الألعاب (عربي بس) ──
@Client.on_callback_query(filters.regex("^cmds_games$"))
async def cmds_games_cb(c: Client, query: CallbackQuery):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("رجوع", callback_data=f"cmds_back_{query.from_user.id}")],
        [InlineKeyboardButton("إغلاق", callback_data="cmds_close")],
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
