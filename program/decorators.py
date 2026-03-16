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


def _get_user_id(message: Message):
    """
    جيب الـ user_id بأمان — يتعامل مع anonymous admins
    """
    if message.from_user:
        return message.from_user.id
    # مشرف مجهول — sender_chat
    if message.sender_chat:
        return message.sender_chat.id
    return None


async def _is_admin(client: Client, message: Message, user_id: int) -> bool:
    """
    تحقق هل المستخدم مشرف في الجروب — بيجرب أكثر من طريقة
    """
    try:
        member = await client.get_chat_member(message.chat.id, user_id)
        status = member.status.value if member.status else ""
        return status in ("administrator", "creator", "owner")
    except Exception:
        pass
    # fallback للكاش
    admins = await get_administrators(message.chat)
    return user_id in admins


def authorized_users_only(func: Callable) -> Callable:
    """
    مشرفين الجروب الحقيقيين + sudo users
    """
    async def decorator(client: Client, message: Message):
        user_id = _get_user_id(message)

        # anonymous admin (sender_chat) — نعتبره مشرف تلقائياً
        if message.sender_chat and not message.from_user:
            return await func(client, message)

        if not user_id:
            return

        # sudo users فوق الكل
        if user_id in SUDO_USERS or is_master(user_id):
            return await func(client, message)

        # تحقق من الجروب
        if await _is_admin(client, message, user_id):
            return await func(client, message)

    return decorator


def sudo_users_only(func: Callable) -> Callable:
    async def decorator(client: Client, message: Message):
        user_id = _get_user_id(message)
        if not user_id:
            return
        if user_id in SUDO_USERS or is_master(user_id):
            return await func(client, message)
    return decorator


def humanbytes(size):
    if not size:
        return ""
    power = 2 ** 10
    raised_to_pow = 0
    dict_power_n = {0: "", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
    while size > power:
        size /= power
        raised_to_pow += 1
    return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"


ADMIN_DEFAULT_PERMS = {"skip", "mute_user", "play", "queue", "search"}


def bot_admin_check(perm: str):
    """
    تحقق من صلاحية معينة:
    - master + sudo: كل حاجة
    - مشرف جروب حقيقي: ADMIN_DEFAULT_PERMS
    - bot admin: الصلاحيات اللي اتحددتله
    """
    def wrapper(func: Callable) -> Callable:
        async def decorator(client: Client, message: Message):
            user_id = _get_user_id(message)

            if message.sender_chat and not message.from_user:
                return await func(client, message)

            if not user_id:
                return

            if user_id in SUDO_USERS or is_master(user_id):
                return await func(client, message)

            chat_id = message.chat.id

            if await _is_admin(client, message, user_id):
                if perm in ADMIN_DEFAULT_PERMS:
                    return await func(client, message)
                else:
                    return await message.reply("❌ الصلاحية دي للبوت ادمن بس")

            if has_permission(chat_id, user_id, perm):
                return await func(client, message)

            await message.reply("❌ مش عندك صلاحية تستخدم الأمر ده")
        return decorator
    return wrapper


def all_members_check(func: Callable) -> Callable:
    async def decorator(client: Client, message: Message):
        return await func(client, message)
    return decorator
