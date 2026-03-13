from pyrogram import filters
from typing import List, Union
from config import COMMAND_PREFIXES

other_filters = filters.group & ~filters.via_bot & ~filters.forwarded
other_filters2 = (
    filters.private & ~filters.via_bot & ~filters.forwarded
)


def command(commands: Union[str, List[str]]):
    return filters.command(commands, COMMAND_PREFIXES)

def command2(commands: Union[str, List[str]]):
    # نفس الـ prefixes — عشان الأوامر العربية تشتغل زي الإنجليزية
    return filters.command(commands, COMMAND_PREFIXES)
