from pyrogram import filters
from typing import List, Union
from config import COMMAND_PREFIXES

# البادئات بدون /
PREFIXES_NO_SLASH = [p for p in COMMAND_PREFIXES if p != "/"]

other_filters = filters.group & ~filters.via_bot & ~filters.forwarded
other_filters2 = (
    filters.private & ~filters.via_bot & ~filters.forwarded
)


def command(commands: Union[str, List[str]]):
    return filters.command(commands, COMMAND_PREFIXES)

def command2(commands: Union[str, List[str]]):
    return filters.command(commands, PREFIXES_NO_SLASH)

def arabic_command(words: List[str]):
    """فلتر بيتحقق إن الرسالة تبدأ بكلمة عربية من غير أي بادئة"""
    async def func(_, __, message):
        if not message.text:
            return False
        text = message.text.strip()
        for word in words:
            if text == word or text.startswith(word + " "):
                return True
        return False
    return filters.create(func)
