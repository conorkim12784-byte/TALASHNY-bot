import os
import re
import sys
import shutil
import subprocess
import traceback

from time import time
from io import StringIO
from sys import version as pyver
from inspect import getfullargspec
from driver.filters import command2, other_filters
from config import BOT_USERNAME as bname
from driver.veez import bot
from pyrogram import Client, filters
from driver.decorators import sudo_users_only, errors
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup


async def aexec(code, client, message):
    exec(
        "async def __aexec(client, message): "
        + "".join(f"\n {a}" for a in code.split("\n"))
    )
    return await locals()["__aexec"](client, message)

async def edit_or_reply(msg: Message, **kwargs):
    func = msg.edit_text if msg.from_user.is_self else msg.reply
    spec = getfullargspec(func.__wrapped__).args
    await func(**{k: v for k, v in kwargs.items() if k in spec})


@Client.on_message(command2(["مغادره البوت"]) & ~filters.edited)
@sudo_users_only
async def bot_leave_group(_, message):
    if len(message.command) != 2:
        await message.reply_text(
            "**usage:**\n\n» /leavebot [chat id]"
        )
        return
    chat = message.text.split(None, 2)[1]
    try:
        await bot.leave_chat(chat)
    except Exception as e:
        await message.reply_text(f"❌ procces failed\n\nreason: `{e}`")
        print(e)
        return
    await message.reply_text(f"✅ Bot successfully left from the Group:\n\n💭 » `{chat}`")
