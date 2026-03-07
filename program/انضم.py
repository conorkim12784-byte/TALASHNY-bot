import asyncio
from driver.veez import user
from pyrogram.types import Message
from pyrogram import Client, filters
from config import BOT_USERNAME, SUDO_USERS
from driver.filters import command, other_filters
from driver.filters import command2, other_filters
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant
from driver.decorators import authorized_users_only, sudo_users_only
from config import SUDO_USERS, ASSISTANT_NAME
from driver.decorators import authorized_users_only, sudo_users_only, errors


@Client.on_message(
    command2(["انضم"]) & other_filters
)
@authorized_users_only
async def join_chat(c: Client, m: Message):
    chat_id = m.chat.id
    try:
        invitelink = await c.export_chat_invite_link(chat_id)
        if invitelink.startswith("https://t.me/+"):
            invitelink = invitelink.replace(
                "https://t.me/+", "https://t.me/joinchat/"
            )
            await user.join_chat(invitelink)
            return await user.send_message(chat_id, "انا جيت اهو يارب مكونش اتٲخرت")
    except UserAlreadyParticipant:
        return await user.send_message(chat_id, "انا موجود هنا😐")