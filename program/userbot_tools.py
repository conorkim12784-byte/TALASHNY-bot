import asyncio

from driver.veez import user
from pyrogram.types import Message
from pyrogram import Client, filters
from pyrogram.errors import (
    ChatAdminRequired,
    InviteHashExpired,
    InviteHashInvalid,
    InviteRequestSent,
    PeerIdInvalid,
    UserAlreadyParticipant,
    UserNotParticipant,
)

from config import SUDO_USERS
from driver.filters import command, command2, other_filters
from driver.decorators import sudo_users_only


def _status_value(status) -> str:
    value = getattr(status, "value", status)
    return str(value).lower()


async def _delete_safe(message: Message):
    try:
        await message.delete()
    except Exception:
        pass


async def _assistant_id() -> int:
    return (await user.get_me()).id


async def _assistant_is_joined(bot_client: Client, chat_id: int) -> bool:
    try:
        member = await bot_client.get_chat_member(chat_id, await _assistant_id())
        return _status_value(member.status) in ("member", "administrator", "creator", "owner", "restricted")
    except UserNotParticipant:
        return False
    except Exception:
        return False


async def _warm_assistant_peer(chat_id: int) -> None:
    try:
        await user.get_chat(chat_id)
    except PeerIdInvalid:
        return
    except Exception:
        return


async def _make_invite_link(bot_client: Client, chat_id: int) -> str:
    try:
        invite = await bot_client.create_chat_invite_link(chat_id)
        return invite.invite_link
    except ChatAdminRequired:
        raise RuntimeError("البوت محتاج صلاحية دعوة المستخدمين عشان يضم الحساب المساعد.")
    except Exception:
        try:
            link = await bot_client.export_chat_invite_link(chat_id)
            if link.startswith("https://t.me/+"):
                link = link.replace("https://t.me/+", "https://t.me/joinchat/")
            return link
        except Exception as e:
            raise RuntimeError(f"فشل إنشاء رابط دعوة للحساب المساعد: {e}")


async def _join_assistant(bot_client: Client, chat_id: int) -> str:
    if await _assistant_is_joined(bot_client, chat_id):
        await _warm_assistant_peer(chat_id)
        return "الحساب المساعد موجود بالفعل في المجموعة"

    link = await _make_invite_link(bot_client, chat_id)
    try:
        await user.join_chat(link)
    except UserAlreadyParticipant:
        await _warm_assistant_peer(chat_id)
        return "الحساب المساعد موجود بالفعل في المجموعة"
    except InviteRequestSent:
        return "تم إرسال طلب انضمام للحساب المساعد. اقبل الطلب من إعدادات المجموعة."
    except (InviteHashExpired, InviteHashInvalid):
        link = await _make_invite_link(bot_client, chat_id)
        try:
            await user.join_chat(link)
        except UserAlreadyParticipant:
            pass
    await _warm_assistant_peer(chat_id)
    return "انضم الحساب المساعد بنجاح"


@Client.on_message(command2(["userbotjoin", "انضم", "انضم_المساعد", "ضم_المساعد"]) & other_filters)
@sudo_users_only
async def join_chat(c: Client, m: Message):
    await _delete_safe(m)
    try:
        result = await _join_assistant(c, m.chat.id)
        return await c.send_message(m.chat.id, result)
    except Exception as e:
        return await c.send_message(m.chat.id, f"فشل انضمام الحساب المساعد: {e}")


@Client.on_message(command2(["userbotleave", "خروج_المساعد", "مغادرة_المساعد"]) & other_filters)
@sudo_users_only
async def leave_chat(c: Client, m: Message):
    await _delete_safe(m)
    chat_id = m.chat.id
    try:
        await user.leave_chat(chat_id)
        return await c.send_message(chat_id, "غادر الحساب المساعد المجموعة بنجاح")
    except UserNotParticipant:
        return await c.send_message(chat_id, "الحساب المساعد خارج المجموعة بالفعل")
    except Exception as e:
        return await c.send_message(chat_id, f"فشل خروج الحساب المساعد: {e}")


@Client.on_message(command(["leaveall"]))
@sudo_users_only
async def leave_all(client, message):
    await _delete_safe(message)
    if message.from_user.id not in SUDO_USERS:
        return

    left = 0
    failed = 0
    msg = await message.reply("Userbot leaving all groups...")
    async for dialog in user.iter_dialogs():
        try:
            await user.leave_chat(dialog.chat.id)
            left += 1
        except BaseException:
            failed += 1
        try:
            await msg.edit(f"Userbot leaving all groups...\n\nLeft: {left}\nFailed: {failed}")
        except Exception:
            pass
        await asyncio.sleep(0.7)
    await msg.delete()
    await client.send_message(message.chat.id, f"Left: {left}\nFailed: {failed}")


@Client.on_message(command2(["تأكد_المساعد", "فحص_المساعد", "assistant_status"]) & other_filters)
@sudo_users_only
async def assistant_status(c: Client, m: Message):
    await _delete_safe(m)
    joined = await _assistant_is_joined(c, m.chat.id)
    text = "الحساب المساعد موجود في المجموعة" if joined else "الحساب المساعد غير موجود في المجموعة"
    await c.send_message(m.chat.id, text)


@Client.on_message(filters.left_chat_member)
async def ubot_leave(c: Client, m: Message):
    bot_id = (await c.get_me()).id
    chat_id = m.chat.id
    left_member = m.left_chat_member
    if left_member and left_member.id == bot_id:
        try:
            await user.leave_chat(chat_id)
        except Exception:
            pass
