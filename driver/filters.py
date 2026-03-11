from pyrogram import filters
from pyrogram.types import Message
from typing import List, Union
from config import COMMAND_PREFIXES

COMMAND_YYYBD = None

# pyrofork removed filters.edited - create it manually
edited = filters.create(lambda _, __, m: bool(m.edit_date) if isinstance(m, Message) else False)

other_filters = filters.group & ~edited & ~filters.via_bot & ~filters.forwarded
other_filters2 = filters.private & ~edited & ~filters.via_bot & ~filters.forwarded


def command(commands: Union[str, List[str]]):
    return filters.command(commands, COMMAND_PREFIXES)

def command2(commands: Union[str, List[str]]):
    return filters.command(commands, COMMAND_YYYBD)
