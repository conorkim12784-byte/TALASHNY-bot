
from config import SUDO_USERS

RANKS = {
    "member":0,
    "admin":1,
    "owner":2,
    "sudo":3
}

async def get_rank(client, chat_id, user_id):
    if user_id in SUDO_USERS:
        return "sudo"
    try:
        m = await client.get_chat_member(chat_id, user_id)
    except:
        return "member"

    if m.status == "creator":
        return "owner"
    if m.status == "administrator":
        return "admin"
    return "member"

def rank_value(rank):
    return RANKS.get(rank,0)

def can_target(actor_rank, target_rank):
    return rank_value(actor_rank) > rank_value(target_rank)
