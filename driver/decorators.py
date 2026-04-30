from pyrogram.types import Message
from pyrogram import Client
from driver.permissions import get_rank, can_target
from config import SUDO_USERS


def _uid(message: Message):
    """يجيب user_id بأمان حتى مع مشرفين مجهولين / channel posts."""
    if message.from_user:
        return message.from_user.id
    if message.sender_chat:
        return message.sender_chat.id
    return None


def sudo_only(func):
    async def wrapper(client: Client, message: Message):
        uid = _uid(message)
        if uid is not None and uid in SUDO_USERS:
            return await func(client, message)
        try:
            await message.reply_text("هذا الامر للمطور فقط")
        except Exception:
            pass
    return wrapper


def owner_only(func):
    async def wrapper(client: Client, message: Message):
        uid = _uid(message)
        if uid is None:
            return
        rank = await get_rank(client, message.chat.id, uid)
        if rank in ("sudo", "owner"):
            return await func(client, message)
        await message.reply_text("هذا الامر لمالك الجروب")
    return wrapper


def admin_only(func):
    async def wrapper(client: Client, message: Message):
        uid = _uid(message)
        if uid is None:
            return
        rank = await get_rank(client, message.chat.id, uid)
        if rank in ("sudo", "owner", "admin"):
            return await func(client, message)
        await message.reply_text("هذا الامر للمشرفين")
    return wrapper


def everyone(func):
    async def wrapper(client: Client, message: Message):
        return await func(client, message)
    return wrapper


def authorized_users_only(func):
    async def wrapper(client: Client, message: Message):
        uid = _uid(message)
        if uid is None:
            return
        rank = await get_rank(client, message.chat.id, uid)
        if rank in ("sudo", "owner", "admin"):
            return await func(client, message)
        await message.reply_text("هذا الامر للمشرفين والمطور فقط")
    return wrapper


def sudo_users_only(func):
    """تم إصلاحه: كان بيكسر مع الإذاعة/المطور لو from_user=None
    (مشرف مجهول، channel post، service message)."""
    async def wrapper(client: Client, message: Message):
        uid = _uid(message)
        if uid is not None and uid in SUDO_USERS:
            return await func(client, message)
        try:
            await message.reply_text("هذا الامر للمطور فقط")
        except Exception:
            pass
    return wrapper


def errors(func):
    async def wrapper(client: Client, message: Message):
        try:
            return await func(client, message)
        except Exception as e:
            try:
                await message.reply_text(f"❌ خطأ: `{e}`")
            except Exception:
                pass
    return wrapper


def humanbytes(size):
    if not size:
        return "0 B"
    power = 2 ** 10
    n = 0
    units = {0: "B", 1: "KB", 2: "MB", 3: "GB", 4: "TB"}
    while size > power and n < 4:
        size /= power
        n += 1
    return f"{round(size, 2)} {units[n]}"


def bot_admin_check(permission=None):
    def decorator(func):
        async def wrapper(client: Client, message: Message):
            try:
                bot_id = (await client.get_me()).id
                bot_member = await client.get_chat_member(message.chat.id, bot_id)
                status = getattr(bot_member.status, "value", str(bot_member.status)).lower()
                if status not in ("administrator", "creator", "owner"):
                    return await message.reply_text("❌ البوت محتاج يكون أدمن عشان يعمل كده")
            except Exception as e:
                print(f"[bot_admin_check error] {e}")
            return await func(client, message)
        return wrapper
    return decorator


def target_rank_check(func):
    """يمنع استخدام الأمر على شخص رتبته أعلى أو مساوية."""
    async def wrapper(client: Client, message: Message):
        actor_id = _uid(message)
        if actor_id is None:
            return
        actor_rank = await get_rank(client, message.chat.id, actor_id)

        target_id = None
        if message.reply_to_message and message.reply_to_message.from_user:
            target_id = message.reply_to_message.from_user.id
        elif len(getattr(message, "command", []) or []) >= 2:
            arg = message.command[1]
            try:
                if arg.lstrip("-").isdigit():
                    target_id = int(arg)
                else:
                    u = await client.get_users(arg)
                    target_id = u.id
            except Exception:
                target_id = None

        if target_id is not None:
            target_rank = await get_rank(client, message.chat.id, target_id)
            if not can_target(actor_rank, target_rank):
                await message.reply_text(
                    "❌ لا يمكنك استخدام هذا الأمر على شخص رتبته أعلى أو مساوية لك"
                )
                return
        return await func(client, message)
    return wrapper
