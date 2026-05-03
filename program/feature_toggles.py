# feature_toggles.py — نظام قفل/فتح أي أمر في البوت
#
# الاستخدام:
#   • قفل امر <اسم الأمر>     → يعطل الأمر داخل الجروب
#   • فتح امر <اسم الأمر>     → يفعّل الأمر تاني
#   • قائمة الاوامر المقفله    → يعرض الأوامر المقفولة في الجروب
#
# يتم حفظ القائمة في ملف JSON محلي.
# المعالجة بتشتغل قبل أي handler تاني (group=-1000) ولو الأمر متعطل
# يتم إيقاف الـ propagation تلقائياً.

import os
import json
from collections import defaultdict
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram import StopPropagation

from driver.filters import command2, other_filters
from driver.botadmin import is_master

DATA_FILE = "feature_toggles.json"

# قائمة الأوامر اللي يمكن قفلها (الاسم العربي/الإنجليزي بدون شرطة)
TOGGLEABLE_COMMANDS = {
    "تشغيل":   ["تشغيل", "شغل", "play", "mplay"],
    "فيديو":   ["فيد", "فيديو", "ستريم", "vplay", "vstream"],
    "بحث":     ["بحث", "يوت", "search"],
    "تحميل":   ["تحميل", "song", "video", "vsong"],
    "تخطي":    ["تخطي", "skip"],
    "انهاء":   ["انهاء", "اسكت", "stop"],
    "ايقاف":   ["ايقاف", "pause"],
    "كمل":     ["كمل", "resume"],
    "ميوت":    ["ميوت", "mute", "فك ميوت", "unmute"],
    "تحكم":    ["تحكم", "صوت", "volume"],
    "كتم":     ["كتم", "فك كتم"],
    "قائمه":   ["قائمه", "queue", "playlist"],
    "بوت":     ["بوت"],
    "بينج":    ["بينج", "ping"],
    "ايدي":    ["ايدي", "id"],
    "زوجني":   ["زوجني", "اتجوز"],
    "زوجي":    ["زوجي", "زوجتي"],
    "طلاق":    ["طلاق"],
    "xo":      ["xo", "اكس"],
    "كت":      ["كت"],
    "صراحة":   ["صراحة", "صراحه"],
    "تاك":     ["تاك"],
    "الهمس":   ["الهمس", "whisper"],
    "اشتراك":  ["اشتراك اجباري", "fsub"],
    "قائمة":   ["قائمه الاوامر", "الاوامر", "اوامر", "commands", "help"],
    "كيبورد":  ["كيبورد", "keyboard"],
    "سيرفر":   ["سيرفر", "sysinfo"],
    "ناو بلي": ["مين مشغل", "np", "nowplaying"],
    "كول":     ["مين في الكول", "incall"],
    "مده":     ["مده التشغيل", "uptime"],
}


def _load() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(d: dict) -> None:
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def is_locked(chat_id: int, key: str) -> bool:
    d = _load()
    return key in d.get(str(chat_id), [])


def _set_lock(chat_id: int, key: str, locked: bool) -> None:
    d = _load()
    arr = set(d.get(str(chat_id), []))
    if locked:
        arr.add(key)
    else:
        arr.discard(key)
    d[str(chat_id)] = sorted(arr)
    _save(d)


async def _is_owner_or_master(c: Client, chat_id: int, user_id: int) -> bool:
    if is_master(user_id):
        return True
    try:
        m = await c.get_chat_member(chat_id, user_id)
        st = getattr(m.status, "value", str(m.status)).lower()
        return st in ("creator", "owner", "administrator")
    except Exception:
        return False


def _resolve_key(name: str) -> str | None:
    name = name.strip().lower()
    for key, aliases in TOGGLEABLE_COMMANDS.items():
        if name == key.lower() or name in [a.lower() for a in aliases]:
            return key
    return None


# ════════════════════════════════════════
# قفل / فتح
# ════════════════════════════════════════
@Client.on_message(command2(["قفل امر", "قفل أمر"]) & other_filters)
async def lock_cmd_feature(c: Client, m: Message):
    if not m.from_user:
        return
    if not await _is_owner_or_master(c, m.chat.id, m.from_user.id):
        return await m.reply("✘ هذا الأمر للمالك / أصحاب البوت فقط")

    parts = (m.text or "").split(maxsplit=2)
    if len(parts) < 3:
        return await m.reply(
            "**الاستخدام:** `قفل امر <اسم الأمر>`\n\n"
            "**مثال:** `قفل امر زوجني`"
        )
    key = _resolve_key(parts[2])
    if not key:
        return await m.reply(f"✘ مفيش أمر بالاسم ده. اكتب `قائمه الاوامر القابله للقفل`")
    _set_lock(m.chat.id, key, True)
    await m.reply(f"🔒 **تم قفل أمر** `{key}` في الجروب")


@Client.on_message(command2(["فتح امر", "فتح أمر"]) & other_filters)
async def unlock_cmd_feature(c: Client, m: Message):
    if not m.from_user:
        return
    if not await _is_owner_or_master(c, m.chat.id, m.from_user.id):
        return await m.reply("✘ هذا الأمر للمالك / أصحاب البوت فقط")

    parts = (m.text or "").split(maxsplit=2)
    if len(parts) < 3:
        return await m.reply("**الاستخدام:** `فتح امر <اسم الأمر>`")
    key = _resolve_key(parts[2])
    if not key:
        return await m.reply("✘ مفيش أمر بالاسم ده")
    _set_lock(m.chat.id, key, False)
    await m.reply(f"🔓 **تم فتح أمر** `{key}` في الجروب")


@Client.on_message(command2(["الاوامر المقفوله", "الاوامر المقفله", "قائمه الاوامر القابله للقفل"]) & other_filters)
async def list_locks(c: Client, m: Message):
    locked = _load().get(str(m.chat.id), [])
    if not locked:
        text = "✔ **مفيش أوامر مقفولة في الجروب**\n\n"
    else:
        text = "🔒 **الأوامر المقفولة:**\n" + "\n".join(f"» `{k}`" for k in locked) + "\n\n"
    text += "**كل الأوامر القابلة للقفل/الفتح:**\n"
    text += " · ".join(f"`{k}`" for k in TOGGLEABLE_COMMANDS.keys())
    await m.reply(text)


# ════════════════════════════════════════
# Middleware يمنع تنفيذ الأوامر المقفولة
# ════════════════════════════════════════
@Client.on_message(filters.group & filters.text, group=-1000)
async def _enforce_locks(c: Client, m: Message):
    if not m.text:
        return
    txt = m.text.strip().lower().lstrip("/")
    if not txt:
        return

    # شيل الـ @botusername لو موجود
    txt = txt.split("@", 1)[0]

    # ابحث عن مطابقة من بداية النص
    locked = _load().get(str(m.chat.id), [])
    if not locked:
        return

    for key in locked:
        for alias in TOGGLEABLE_COMMANDS.get(key, []):
            a = alias.lower()
            if txt == a or txt.startswith(a + " "):
                try:
                    await m.reply(f"🔒 **أمر** `{key}` **مقفول في الجروب**")
                except Exception:
                    pass
                raise StopPropagation
