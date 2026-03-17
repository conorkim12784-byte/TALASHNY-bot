# driver/botadmin.py — نظام Bot Admin

from collections import defaultdict
from config import SUDO_USERS

BOT_ADMINS: dict = defaultdict(dict)
MASTER_ID = 1923931101

ALL_PERMISSIONS = {
    "play":       "تشغيل موسيقى وفيديو",
    "skip":       "تخطي وايقاف",
    "queue":      "عرض القايمة",
    "download":   "تحميل اغاني وفيديوهات",
    "search":     "بحث يوتيوب",
    "volume":     "التحكم في الصوت",
    "lock":       "قفل وفتح الجروب",
    "mute_user":  "كتم المستخدمين",
    "vcinfo":     "معلومات الكول",
    "promote":    "رفع بوت ادمنز",
}


def is_master(user_id: int) -> bool:
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


def add_bot_admin(chat_id: int, user_id: int, perms: set):
    BOT_ADMINS[chat_id][user_id] = perms


def remove_bot_admin(chat_id: int, user_id: int):
    if chat_id in BOT_ADMINS and user_id in BOT_ADMINS[chat_id]:
        del BOT_ADMINS[chat_id][user_id]


def get_bot_admins(chat_id: int) -> dict:
    return BOT_ADMINS.get(chat_id, {})


def get_permissions(chat_id: int, user_id: int) -> set:
    return BOT_ADMINS.get(chat_id, {}).get(user_id, set())
