from typing import List

from pyrogram.enums import ChatMemberStatus
try:
    from pyrogram.enums import ChatMembersFilter
except Exception:
    ChatMembersFilter = None  # type: ignore
from pyrogram.types import Chat

from cache.admins import get as cache_get, set as cache_set


def _status_value(status) -> str:
    value = getattr(status, "value", status)
    return str(value).lower()


def _is_admin_or_owner(status) -> bool:
    try:
        if status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            return True
    except Exception:
        pass
    return _status_value(status) in ("administrator", "admin", "creator", "owner")


async def _collect_admins(chat: Chat, filter_value=None) -> List[int]:
    administrators: List[int] = []
    try:
        kwargs = {"filter": filter_value} if filter_value is not None else {}
        async for member in chat.get_members(**kwargs):
            user = getattr(member, "user", None)
            if user and not getattr(user, "is_bot", False) and _is_admin_or_owner(getattr(member, "status", None)):
                administrators.append(int(user.id))
    except Exception as e:
        print(f"[collect_admins error] {e}")
    return administrators


async def get_administrators(chat: Chat) -> List[int]:
    cached = cache_get(chat.id)
    if cached:
        return cached

    administrators: List[int] = []

    if ChatMembersFilter is not None:
        administrators = await _collect_admins(chat, ChatMembersFilter.ADMINISTRATORS)

    if not administrators:
        administrators = await _collect_admins(chat, "administrators")

    if not administrators:
        administrators = await _collect_admins(chat)

    administrators = list(dict.fromkeys(administrators))
    cache_set(chat.id, administrators)
    return administrators


async def refresh_administrators(chat: Chat) -> List[int]:
    administrators: List[int] = []

    if ChatMembersFilter is not None:
        administrators = await _collect_admins(chat, ChatMembersFilter.ADMINISTRATORS)

    if not administrators:
        administrators = await _collect_admins(chat, "administrators")

    if not administrators:
        administrators = await _collect_admins(chat)

    administrators = list(dict.fromkeys(administrators))
    cache_set(chat.id, administrators)
    return administrators
