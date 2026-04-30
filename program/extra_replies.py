# extra_replies.py — أمر "بوت" (الرد العشوائي) فقط.
# أمر "المالك" نُقل إلى program/owner_change.py عشان نقدر نغير
# يوزر المالك بالأمر "تغيير يوزر المالك".

import random
from pyrogram import Client, filters
from pyrogram.types import Message
from driver.filters import command2, other_filters


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


@Client.on_message(command2(["بوت", "البوت"]) & other_filters)
async def bot_reply(client: Client, message: Message):
    try:
        await client.send_reaction(
            chat_id=message.chat.id,
            message_id=message.id,
            emoji="❤",
        )
    except Exception:
        pass

    reply = random.choice(RANDOM_REPLIES)
    await message.reply_text(reply, quote=True)
