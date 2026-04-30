from pyrogram import filters
from typing import List, Union
from config import COMMAND_PREFIXES

# الأوامر العربية كانت بتستخدم prefixes=None وده بيمنع pyrogram من
# مطابقة أي أمر، فبقت كل الأوامر العربية (اذاعه/حد_الحظر/رفع/...) ميتة.
# الحل: نمرّر نفس COMMAND_PREFIXES + سلسلة فاضية "" عشان يقبل
# الأوامر اللي بتتكتب من غير برفكس (زي: اذاعه، حد_الحظر).
COMMAND_YYYBD = COMMAND_PREFIXES + [""]

other_filters = filters.group & ~filters.via_bot & ~filters.forwarded
other_filters2 = (
    filters.private & ~filters.via_bot & ~filters.forwarded
)


def command(commands: Union[str, List[str]]):
    return filters.command(commands, COMMAND_PREFIXES)


def command2(commands: Union[str, List[str]]):
    return filters.command(commands, COMMAND_YYYBD)
