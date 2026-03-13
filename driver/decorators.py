from typing import Callable
from pyrogram import Client
from pyrogram.types import Message
from config import SUDO_USERS
from driver.admins import get_administrators
from driver.botadmin import has_permission, is_master



def errors(func: Callable) -> Callable:
    async def decorator(client: Client, message: Message):
        try:
            return await func(client, message)
        except Exception as e:
            await message.reply(f"{type(e).__name__}: {e}")

    return decorator


def authorized_users_only(func: Callable) -> Callable:
    async def decorator(client: Client, message: Message):
        if message.from_user.id in SUDO_USERS:
            return await func(client, message)

        administrators = await get_administrators(message.chat)

        for administrator in administrators:
            if administrator == message.from_user.id:
                return await func(client, message)

    return decorator


def sudo_users_only(func: Callable) -> Callable:
    async def decorator(client: Client, message: Message):
        if message.from_user.id in SUDO_USERS:
            return await func(client, message)

    return decorator


def humanbytes(size):
    """Convert Bytes To Bytes So That Human Can Read It"""
    if not size:
        return ""
    power = 2 ** 10
    raised_to_pow = 0
    dict_power_n = {0: "", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
    while size > power:
        size /= power
        raised_to_pow += 1
    return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"


# الصلاحيات اللي مشرف الجروب الحقيقي بيقدر يستخدمها تلقائياً
ADMIN_DEFAULT_PERMS = {"play", "skip", "mute_user"}


def bot_admin_check(perm: str):
    """
    decorator للتحقق من صلاحية معينة:
    - ماستر وسودو: كل حاجة
    - مشرف جروب حقيقي: play + skip + mute_user بس
    - بوت ادمن: الصلاحيات اللي اتحددتله بس
    """
    def wrapper(func: Callable) -> Callable:
        async def decorator(client: Client, message: Message):
            user_id = message.from_user.id
            chat_id = message.chat.id

            # ماستر وسودو — فوق الكل
            if user_id in SUDO_USERS or is_master(user_id):
                return await func(client, message)

            # مشرف جروب حقيقي — بس صلاحيات محددة
            administrators = await get_administrators(message.chat)
            if user_id in administrators:
                if perm in ADMIN_DEFAULT_PERMS:
                    return await func(client, message)
                else:
                    return await message.reply("❌ الصلاحية دي للبوت ادمن بس")

            # بوت ادمن عنده الصلاحية دي
            if has_permission(chat_id, user_id, perm):
                return await func(client, message)

            await message.reply("❌ مش عندك صلاحية تستخدم الامر ده")
        return decorator
    return wrapper
