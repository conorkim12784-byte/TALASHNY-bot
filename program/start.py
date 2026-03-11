import asyncio

from datetime import datetime
from sys import version_info
from time import time

from config import (
    BOT_PHOTO,
    ALIVE_IMG,
    ALIVE_NAME,
    BOT_NAME,
    BOT_USERNAME,
    GROUP_SUPPORT,
    OWNER_NAME,
    SUDO_USERS,
    BOT_TOKEN,
    DEV_PHOTO,
    DEV_NAME,
    UPDATES_CHANNEL,
)
from program import __version__
from driver.veez import user
from driver.filters import command, other_filters
from driver.decorators import sudo_users_only
from driver.database.dbchat import add_served_chat, is_served_chat
from driver.database.dbpunish import is_gbanned_user
from pyrogram import Client, filters, __version__ as pyrover
from pyrogram.errors import FloodWait, MessageNotModified
from pytgcalls import (__version__ as pytover)
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, ChatJoinRequest

__major__ = 0
__minor__ = 2
__micro__ = 1

__python_version__ = f"{version_info[0]}.{version_info[1]}.{version_info[2]}"

START_TIME = datetime.utcnow()
START_TIME_ISO = START_TIME.replace(microsecond=0).isoformat()
TIME_DURATION_UNITS = (
    ("week", 60 * 60 * 24 * 7),
    ("day", 60 * 60 * 24),
    ("hour", 60 * 60),
    ("min", 60),
    ("sec", 1),
)


async def _human_time_duration(seconds):
    if seconds == 0:
        return "inf"
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append("{} {}{}".format(amount, unit, "" if amount == 1 else "s"))
    return ", ".join(parts)


@Client.on_message(command("start") & filters.private)
async def start_(client: Client, message: Message):
    await message.delete()
    await message.reply_photo(
        photo=f"{BOT_PHOTO}",
        caption=f"""**━━━━━━━━━━━━
اهلا يبني {message.from_user.mention()} !
مرحبا بك انا بوت اقوم بتشغيل الاغاني في المكالمه الصوتية.
يمكنني التشغيل بصوت رائع وبدون اي مشاكل او تقطيع في الاغنيه
 + اضفني الى مجموعتك وارفعني رول بشكل مع كامل الصلاحيات
 البوت يشتغل بالاوامر عربي وانجليزي
 لانضمام الحساب المساعد لتشغيل البوت اكتب انضم


  لمعرفة استخدامي بشكل صحيح اضغط علي زر الاوامر. DEV [TALASHNY](https://t.me/FY_TF)

━━━━━━━━━━━━━━━━━━**""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "ضيف البوت لمجموعتك",
                        url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
                    )
                ],
                [InlineKeyboardButton("", callback_data="cbhowtouse")],
                [
                    InlineKeyboardButton(
                        "الاوامر", url=f"https://telegra.ph/%F0%9D%99%B2%E1%B4%8F%E1%B4%8D%E1%B4%8D%E1%B4%80%C9%B4%E1%B4%85s-04-06"),
                    InlineKeyboardButton("المطور", url=f"https://t.me/{OWNER_NAME}"),
                ],
                [
                    InlineKeyboardButton(
                        "جروب الدعم", url=f"https://t.me/{GROUP_SUPPORT}"
                    ),
                    InlineKeyboardButton(
                        "قناة البوت", url=f"https://t.me/{UPDATES_CHANNEL}"
                    ),
                ],
            ]
        ),
    )


@Client.on_message(command(["source"]) & filters.group)
async def source_cmd(client: Client, message: Message):
    await message.delete()
    await message.reply_photo(
        photo="https://i.postimg.cc/wxV3PspQ/1756574872401.gif",
        caption="PROGRAMMER [DEVELOPER](https://t.me/FY_TF)\nTO COMMUNICATE TOGETHER\nFOLLOW THE BUTTONS LOWER",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("اضف البوت الى مجموعتك", url=f"https://t.me/{BOT_USERNAME}?startgroup=true"),
                ]
            ]
        )
    )


@Client.on_message(command(["developer", "dev"]) & filters.group)
async def dev_cmd(client: Client, message: Message):
    await message.delete()
    await message.reply_photo(
        photo="https://i.postimg.cc/wxV3PspQ/1756574872401.gif",
        caption="مش محتاجين نكتب كلام كتير خش ع اول زرار وانت هتعرف",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("DEVELOPER", url="https://t.me/FY_TF"),
                ],
                [
                    InlineKeyboardButton("ضيف البوت لمجموعتك", url=f"https://t.me/{BOT_USERNAME}?startgroup=true"),
                ]
            ]
        )
    )


@Client.on_message(command(["لب التوكن", "لب_التوكن", "scolze"]) & filters.private)
@sudo_users_only
async def shadow(c: Client, message: Message):
    start = time()
    m_reply = await message.reply_text("انتظر من فضلك...")
    BOT_TOKEN = time() - start
    await m_reply.edit_text(f"**تم جلب التوكن**\n`{BOT_TOKEN}`")


@Client.on_message(command(["ping"]))
async def ping_pong(client: Client, message: Message):
    await message.delete()
    start = time()
    m_reply = await message.reply_text("pinging...")
    delta_ping = time() - start
    await m_reply.edit_text(f"PONG!!\n`{delta_ping * 1000:.3f} ms`")


@Client.on_message(command(["uptime", f"uptime@{BOT_USERNAME}"]))
async def get_uptime(client: Client, message: Message):
    await message.delete()
    current_time = datetime.utcnow()
    uptime_sec = (current_time - START_TIME).total_seconds()
    uptime = await _human_time_duration(int(uptime_sec))
    await message.reply_text(
        "bot status:\n"
        f"uptime: `{uptime}`\n"
        f"start time: `{START_TIME_ISO}`"
    )


@Client.on_chat_join_request()
async def approve_join_chat(c: Client, m: ChatJoinRequest):
    if not m.from_user:
        return
    try:
        await c.approve_chat_join_request(m.chat.id, m.from_user.id)
    except FloodWait as e:
        await asyncio.sleep(e.x + 2)
        await c.approve_chat_join_request(m.chat.id, m.from_user.id)


@Client.on_message(filters.new_chat_members)
async def new_chat(c: Client, m: Message):
    chat_id = m.chat.id
    if await is_served_chat(chat_id):
        pass
    else:
        await add_served_chat(chat_id)
    ass_uname = (await user.get_me()).username
    bot_id = (await c.get_me()).id
    for member in m.new_chat_members:
        if member.id == bot_id:
            return await m.reply(
                "**شكرا لاضافتي الى المجموعة !**\n\n"
                "قم بترقيتي كمسؤول عن المجموعة لكي اتمكن من العمل بشكل صحيح\n"
                "ولا تنسى كتابة `/انضم` لدعوة الحساب المساعد\n"
                "قم بكتابة `/تحديث` لتحديث قائمة المشرفين",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("قناة البوت", url=f"https://t.me/{UPDATES_CHANNEL}"),
                            InlineKeyboardButton("جروب الدعم", url=f"https://t.me/{GROUP_SUPPORT}")
                        ],
                        [
                            InlineKeyboardButton(ALIVE_NAME, url=f"https://t.me/{ass_uname}"),
                        ],
                        [
                            InlineKeyboardButton(
                                "اضف البوت لمجموعتك",
                                url=f'https://t.me/{BOT_USERNAME}?startgroup=true'),
                        ],
                    ]
                )
            )


chat_watcher_group = 5


@Client.on_message(group=chat_watcher_group)
async def chat_watcher_func(_, message: Message):
    try:
        userid = message.from_user.id
    except Exception:
        return
    suspect = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
    if await is_gbanned_user(userid):
        try:
            await message.chat.ban_member(userid)
        except Exception:
            return
        await message.reply_text(
            f"({suspect})\n\n**Gbanned** user detected, that user has been gbanned by sudo user and was blocked from this Chat !\n\n**Reason:** potential spammer and abuser."
        )
