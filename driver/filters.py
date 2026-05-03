from pyrogram import filters
from typing import List, Union
import re

from config import COMMAND_PREFIXES

# ─────────────────────────────────────────────
# الأوامر العربية كانت بتستخدم prefixes=None وده بيمنع pyrogram من
# مطابقة أي أمر، فبقت كل الأوامر العربية (اذاعه/حد_الحظر/رفع/...) ميتة.
# الحل: نمرّر نفس COMMAND_PREFIXES + سلسلة فاضية "" عشان يقبل
# الأوامر اللي بتتكتب من غير برفكس (زي: اذاعه، حد_الحظر).
# ─────────────────────────────────────────────
COMMAND_YYYBD = COMMAND_PREFIXES + [""]

other_filters = filters.group & ~filters.via_bot & ~filters.forwarded
other_filters2 = (
    filters.private & ~filters.via_bot & ~filters.forwarded
)


def command(commands: Union[str, List[str]]):
    return filters.command(commands, COMMAND_PREFIXES)


def command2(commands: Union[str, List[str]]):
    return filters.command(commands, COMMAND_YYYBD)


# ─────────────────────────────────────────────
# phrases(): فلتر للأوامر اللي فيها مسافات (متعددة الكلمات).
# filters.command ما بيشتغلش معاها لأنه بيقسم النص على المسافات.
# الفلتر ده بيطابق أول الرسالة بـ regex مع كلمة واحدة أو أكثر.
# مثال: phrases(["تفعيل التاك", "صراحة معاك"])
# ─────────────────────────────────────────────
def phrases(items: Union[str, List[str]]):
    if isinstance(items, str):
        items = [items]
    # أطول جملة الأول عشان "صراحة معاك" يتطابق قبل "صراحة"
    pats = sorted({s.strip() for s in items if s and s.strip()},
                  key=lambda s: -len(s))
    escaped = "|".join(re.escape(p) for p in pats)
    # السماح ببرفكس اختياري + الجملة + (نهاية أو مسافة قبل أي حاجة)
    pref = "".join(re.escape(p) for p in COMMAND_PREFIXES)
    pat = rf"^[{pref}]?(?:{escaped})(?:\s|$)"
    return filters.regex(pat)
