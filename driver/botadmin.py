# driver/botadmin.py — نظام المدير (Manager) داخل البوت
#
# تم إعادة هيكلة الصلاحيات لتغطية كل أوامر البوت تلقائيًا عبر فئات (Categories).
# المالك / صاحب البوت يقدر يحدد بالظبط أي فئة يقدر المدير يستخدمها.
#
# مهم جدًا:
#   • صلاحية "promote_managers" هي اللي تخلي المدير قادر يرفع مديرين تانيين
#     أو يعدّل صلاحياتهم. من غيرها مش هيقدر.
#   • is_master() = المالك الرسمي (MASTER_ID) أو SUDO_USERS فقط.

from collections import defaultdict
from config import SUDO_USERS

BOT_ADMINS: dict = defaultdict(dict)   # {chat_id: {user_id: set(perms)}}
MASTER_ID = 1923931101


# ════════════════════════════════════════════════════════════════
# فئات الصلاحيات — كل فئة بتغطي مجموعة أوامر فعلية في البوت
# الـ key هو اللي بيتحفظ، والـ label هو النص اللي يظهر على الزر.
# ════════════════════════════════════════════════════════════════
ALL_PERMISSIONS = {
    # ── تشغيل وسائط ──
    "play":            "تشغيل موسيقى",
    "vplay":           "تشغيل فيديو وستريم",
    "queue":           "قائمة التشغيل",
    "skip":            "تخطي وايقاف وانهاء",
    "pause_resume":    "ايقاف مؤقت واستكمال",
    "volume":          "التحكم في الصوت",
    "vcinfo":          "معلومات الكول والمشغل",

    # ── بحث وتحميل ──
    "search":          "بحث يوتيوب",
    "download":        "تحميل اغاني وفيديوهات",
    "song_lyric":      "اغنية وكلمات (song/lyric)",

    # ── إدارة الجروب (للمشرفين) ──
    "lock_unlock":     "قفل وفتح الجروب",
    "mute_user":       "كتم وفك كتم المستخدمين",
    "broadcast":       "اذاعة ونشر",

    # ── أدوات ومعلومات ──
    "id_tools":        "ايدي وادوات المعلومات",
    "sysinfo":         "معلومات السيرفر والبنج",
    "keyboard":        "كيبورد تلاشاني",

    # ── تاك ومنشن ──
    "tag":             "أمر التاك (منشن الأعضاء)",

    # ── صلاحيات حساسة (المدير لا يستطيع منحها لنفسه) ──
    "promote_managers": "رفع مديرين وتعديل صلاحياتهم",
    "manage_bot":       "تحديث / ريستارت / مغادرة البوت",
}


# الصلاحيات اللي ممنوع المدير العادي يمنحها لمدير تاني،
# حتى لو هو نفسه عنده promote_managers — دي لازم بس من المالك/سوبر.
RESTRICTED_PERMISSIONS = {"manage_bot"}


def is_master(user_id: int) -> bool:
    """المالك الرسمي أو أحد أصحاب البوت (SUDO)."""
    return user_id == MASTER_ID or user_id in SUDO_USERS


def is_bot_admin(chat_id: int, user_id: int) -> bool:
    return user_id in BOT_ADMINS.get(chat_id, {})


def has_permission(chat_id: int, user_id: int, perm: str) -> bool:
    if is_master(user_id):
        return True
    admins = BOT_ADMINS.get(chat_id, {})
    if user_id not in admins:
        return False
    return perm in admins[user_id]


def can_promote_managers(chat_id: int, user_id: int) -> bool:
    """هل المستخدم ده مسموح له يرفع/ينزّل مديرين؟"""
    if is_master(user_id):
        return True
    return has_permission(chat_id, user_id, "promote_managers")


def add_bot_admin(chat_id: int, user_id: int, perms: set):
    BOT_ADMINS[chat_id][user_id] = set(perms)


def remove_bot_admin(chat_id: int, user_id: int):
    if chat_id in BOT_ADMINS and user_id in BOT_ADMINS[chat_id]:
        del BOT_ADMINS[chat_id][user_id]


def get_bot_admins(chat_id: int) -> dict:
    return BOT_ADMINS.get(chat_id, {})


def get_permissions(chat_id: int, user_id: int) -> set:
    return set(BOT_ADMINS.get(chat_id, {}).get(user_id, set()))
