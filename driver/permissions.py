from config import SUDO_USERS

RANKS = {
    "member": 0,
    "admin": 1,
    "owner": 2,
    "sudo": 3,
}


def _status_str(status) -> str:
    """Pyrogram v2 بيرجع Enum (ChatMemberStatus). كنا بنقارن بـ string
    فدايماً بيفشل ويرجع member. الحل: نطلع value الـ Enum."""
    if status is None:
        return ""
    val = getattr(status, "value", None)
    if val is not None:
        return str(val).lower()
    return str(status).lower()


async def get_rank(client, chat_id, user_id):
    if user_id is None:
        return "member"
    if user_id in SUDO_USERS:
        return "sudo"
    try:
        m = await client.get_chat_member(chat_id, user_id)
    except Exception:
        return "member"

    s = _status_str(m.status)
    if s in ("creator", "owner"):
        return "owner"
    if s in ("administrator", "admin"):
        return "admin"
    return "member"


def rank_value(rank):
    return RANKS.get(rank, 0)


def can_target(actor_rank, target_rank):
    return rank_value(actor_rank) > rank_value(target_rank)
