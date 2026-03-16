from pyrogram.enums import ChatMembersFilter
from typing import List
from pyrogram.types import Chat
from cache.admins import get as cache_get, set as cache_set


async def get_administrators(chat: Chat) -> List[int]:
    """
    جيب كل المشرفين في الجروب — بدون فلترة على صلاحية معينة
    بيرجع list من الـ IDs
    """
    cached = cache_get(chat.id)
    if cached:
        return cached

    administrators = []
    try:
        async for member in chat.get_members(filter=ChatMembersFilter.ADMINISTRATORS):
            user = member.user
            if user and not user.is_bot:
                administrators.append(user.id)
    except Exception as e:
        print(f"[get_administrators error] {e}")

    cache_set(chat.id, administrators)
    return administrators


async def refresh_administrators(chat: Chat) -> List[int]:
    """تحديث الكاش بالقوة"""
    cache_set(chat.id, [])
    return await get_administrators(chat)
