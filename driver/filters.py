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
    """أوامر إنجليزية — بكل البادئات مع /"""
    return filters.command(commands, COMMAND_PREFIXES)


def command2(commands: Union[str, List[str]]):
    """أوامر عربية — بالبادئات بدون /"""
    return filters.command(commands, PREFIXES_NO_SLASH)


def arabic_command(words: List[str]):
    """
    أوامر عربية بدون أي بادئة خالص
    مثال: شغل اغنية  /  تخطي  /  انهاء
    """
    async def func(_, __, message):
        if not message.text:
            return False
        text = message.text.strip()
        for word in words:
            if text == word or text.startswith(word + " "):
                return True
        return False
    return filters.create(func)


def get_query(message, command_words: List[str]) -> str:
    """
    يستخرج الكويري من الرسالة سواء جت من command2 أو arabic_command
    مثال: "شغل اغنية حلوة" → "اغنية حلوة"
    """
    text = message.text.strip() if message.text else ""
    for word in command_words:
        if text.startswith(word + " "):
            return text[len(word):].strip()
        if text == word:
            return ""
    if message.command and len(message.command) > 1:
        return message.text.split(None, 1)[1].strip()
    return ""
