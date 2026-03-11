from pyrogram.enums import ChatMembersFilter
from typing import List
from pyrogram.types import Chat
from cache.admins import get as gett, set


async def get_administrators(chat: Chat) -> List[int]:
    get = gett(chat.id)

    if get:
        return get
    else:
        administrators = []
        async for member in chat.get_members(filter=ChatMembersFilter.ADMINISTRATORS):
            if member.privileges and member.privileges.can_manage_video_chats:
                administrators.append(member.user.id)

        set(chat.id, administrators)
        return administrators
