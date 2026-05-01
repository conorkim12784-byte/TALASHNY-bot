# extra_replies.py — أمر "بوت" مع رد مختلف لأصحاب البوت (SUDO_USERS).
# أمر "المالك" موجود في program/owner_change.py.

import random
from pyrogram import Client, filters
from pyrogram.types import Message
from driver.filters import command2, other_filters

try:
    from config import SUDO_USERS
except Exception:
    SUDO_USERS = []


# الردود العادية للأعضاء
RANDOM_REPLIES = [
    "عاوز إيه يا قمر ؟",
    "نعم حبيبي قول",
    "انا تحت امرك",
    "ليه يا غالي",
    "ايوه قول كده",
    "حاضر يا باشا",
    "انا معاك قول",
    "ها عاوز اي",
    "اقولك على حاجة ؟",
    "انا سامعك يا حلو",
    "امرك يا كبير",
    "بقولك ايه ، احكي",
]

# ردود مخصوصة لأصحاب البوت / المطورين
SUDO_REPLIES = [
    "ايوه يا مبرمجي 🔥",
    "ايوه هو ده اللي برمجني 😏",
    "أمرك يا أسطورة 💎",
    "أنا في خدمتك يا بوس 🔥",
    "نعم يا صانعي 🛠️",
    "ايوه يا باشا، مش ناوي تضفلي أوامر جديدة ولا إيه؟ 😎",
    "هلا بصاحب البوت 🔥",
    "تحت أمرك يا كبير 💎",
]


def _is_sudo(user_id: int) -> bool:
    if not user_id:
        return False
    try:
        return int(user_id) in [int(x) for x in (SUDO_USERS or [])]
    except Exception:
        return False


@Client.on_message(command2(["بوت", "البوت"]) & other_filters)
async def bot_reply(client: Client, message: Message):
    is_sudo = bool(message.from_user) and _is_sudo(message.from_user.id)

    # رياكشن — 🔥 للسودو ❤ للأعضاء
    try:
        await client.send_reaction(
            chat_id=message.chat.id,
            message_id=message.id,
            emoji="🔥" if is_sudo else "❤",
        )
    except Exception:
        pass

    pool = SUDO_REPLIES if is_sudo else RANDOM_REPLIES
    reply = random.choice(pool)
    await message.reply_text(reply, quote=True)
