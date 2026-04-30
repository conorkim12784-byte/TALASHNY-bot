# owner_change.py — أمر "تغيير يوزر المالك"
#
# الفكرة:
# - فيه "مالك رسمي" دايماً = SUDO_USERS من config (أصحاب البوت).
# - فيه "مالك معروض" (DISPLAYED_OWNER) — اللي بتظهر بياناته لما حد يكتب "المالك".
# - الأمر "تغيير يوزر المالك" يعدل DISPLAYED_OWNER فقط.
# - من يستطيع تنفيذ الأمر؟ SUDO_USERS (أصحاب البوت) + المالك المعروض الحالي.
#   يعني المالك الحالي المعروض يقدر ينقل العرض لحد تاني، لكن لو
#   اتغير ميقدرش يرجّعه لنفسه (ده مطلب الصاحب).
#
# الاستخدام:
#   تغيير يوزر المالك              -> يطلب يوزر/آيدي
#   تغيير يوزر المالك @username
#   تغيير يوزر المالك 123456789
#   تغيير يوزر المالك  (بالرد على رسالة)

import json
import os
import random
from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from pyrogram.enums import ChatMemberStatus

from driver.filters import command, command2, other_filters2, other_filters
from config import SUDO_USERS

# ─────────────────────────────────────────────
# تخزين دائم بسيط في ملف JSON
# ─────────────────────────────────────────────
STORE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "owner_state.json")


def _load() -> dict:
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    try:
        with open(STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[owner_change save warn] {e}")


def get_displayed_owner_id() -> Optional[int]:
    data = _load()
    val = data.get("displayed_owner_id")
    return int(val) if val else None


def set_displayed_owner_id(uid: int) -> None:
    data = _load()
    data["displayed_owner_id"] = int(uid)
    _save(data)


# ─────────────────────────────────────────────
# جلسات حوار "اكتب اليوزر"
# ─────────────────────────────────────────────
# user_id -> bool (في انتظار اليوزر)
_pending: dict = {}


def _is_authorized(user_id: int) -> bool:
    """مين يقدر يغير يوزر المالك."""
    if user_id in SUDO_USERS:
        return True
    current = get_displayed_owner_id()
    if current is not None and user_id == current:
        return True
    return False


# ─────────────────────────────────────────────
# الأمر الرئيسي
# ─────────────────────────────────────────────
@Client.on_message(
    (command(["setowner", "changeowner"])
     | command2(["تغيير يوزر المالك", "تغيير_يوزر_المالك", "تغيير المالك"]))
    & (filters.group | filters.private)
)
async def change_owner_cmd(c: Client, m: Message):
    if not m.from_user:
        return
    if not _is_authorized(m.from_user.id):
        return await m.reply("❌ هذا الأمر لأصحاب البوت أو المالك الحالي فقط")

    target_id = await _resolve_target(c, m)
    if target_id is None:
        # نحط حالة انتظار للرد على الرسالة
        _pending[m.from_user.id] = True
        return await m.reply(
            "🔧 **تغيير يوزر المالك**\n\n"
            "ابعت اليوزر أو الآيدي بتاع المالك الجديد دلوقتي\n"
            "(أو رد على رسالته بنفس الأمر)\n\n"
            "للإلغاء اكتب: `الغاء`"
        )

    await _do_change(c, m, target_id)


@Client.on_message(filters.text & ~filters.via_bot, group=8)
async def _await_owner_input(c: Client, m: Message):
    """يلتقط رد المستخدم لو في حالة انتظار."""
    if not m.from_user:
        return
    uid = m.from_user.id
    if not _pending.get(uid):
        return

    txt = (m.text or "").strip()
    if not txt:
        return
    if txt.lower() in ("الغاء", "إلغاء", "cancel"):
        _pending.pop(uid, None)
        return await m.reply("✘ تم الإلغاء")

    # نتجاهل أوامر أخرى
    if txt.startswith(("/", "!", ".")):
        return

    target_id = None
    if txt.lstrip("-").isdigit():
        target_id = int(txt)
    else:
        try:
            u = await c.get_users(txt.lstrip("@"))
            target_id = u.id
        except Exception:
            return await m.reply("✘ مش لاقي اليوزر ده، جرب تاني أو اكتب `الغاء`")

    _pending.pop(uid, None)
    await _do_change(c, m, target_id)


async def _resolve_target(c: Client, m: Message) -> Optional[int]:
    if m.reply_to_message and m.reply_to_message.from_user:
        return m.reply_to_message.from_user.id
    if len(m.command) >= 2:
        arg = m.command[1].lstrip("@")
        if arg.lstrip("-").isdigit():
            return int(arg)
        try:
            u = await c.get_users(arg)
            return u.id
        except Exception:
            return None
    return None


async def _do_change(c: Client, m: Message, target_id: int):
    try:
        u = await c.get_users(target_id)
    except Exception:
        return await m.reply("✘ تعذر جلب بيانات اليوزر")

    if u.is_bot:
        return await m.reply("✘ مينفعش بوت")

    set_displayed_owner_id(target_id)
    await m.reply(
        f"✔ **تم تغيير يوزر المالك المعروض**\n\n"
        f"👑 المالك الجديد: [{u.first_name}](tg://user?id={u.id})\n"
        f"🆔 `{u.id}`\n\n"
        f"دلوقتي لما حد يكتب `المالك` هتظهر بياناته."
    )


# ─────────────────────────────────────────────
# أمر "المالك" — يعرض المالك المعروض (لو متعيّن)،
# وإلا يرجع للسلوك القديم (creator الجروب).
# هنا نستبدل النسخة القديمة من extra_replies.py
# ─────────────────────────────────────────────
async def _get_group_creator(client: Client, chat_id: int):
    try:
        async for member in client.get_chat_members(
            chat_id, filter=__import__("pyrogram").enums.ChatMembersFilter.ADMINISTRATORS
        ):
            if member.status == ChatMemberStatus.OWNER:
                return member.user
    except Exception:
        pass
    return None


@Client.on_message(command2(["المالك", "مالك", "صاحب البوت", "صاحب_البوت"]) & (filters.group | filters.private), group=2)
async def show_owner(client: Client, message: Message):
    """يعرض بيانات المالك المعروض إن وُجد، وإلا creator الجروب."""
    try:
        await message.delete()
    except Exception:
        pass

    target = None
    displayed = get_displayed_owner_id()
    if displayed:
        try:
            target = await client.get_users(displayed)
        except Exception:
            target = None

    if target is None and message.chat and message.chat.type and message.chat.type.value in ("group", "supergroup"):
        target = await _get_group_creator(client, message.chat.id)

    if target is None:
        return await message.reply_text("**تعذر جلب بيانات المالك**")

    # البايو
    bio_text = ""
    try:
        full = await client.get_chat(target.id)
        bio_text = getattr(full, "bio", "") or ""
    except Exception:
        bio_text = ""

    first_name = target.first_name or "المالك"
    mention = f"[{first_name}](tg://user?id={target.id})"
    bio_line = f"**البايو:** `{bio_text}`" if bio_text else "**البايو:** `لا يوجد`"

    caption = (
        "**╭────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁────⟤**\n"
        f"**│ ** {mention}\n"
        f"**│ {bio_line}**\n"
        f"**│ ID:** `{target.id}`\n"
        "**╰────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁────⟤**"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🟢 {first_name}", url=f"tg://user?id={target.id}")],
    ])

    sent_photo = False
    try:
        async for photo in client.get_chat_photos(target.id, limit=1):
            await message.reply_photo(
                photo=photo.file_id,
                caption=caption,
                reply_markup=keyboard,
            )
            sent_photo = True
            break
    except Exception:
        sent_photo = False

    if not sent_photo:
        await message.reply_text(
            caption + "\n\n**ملاحظة:** لا توجد صورة بروفايل ظاهرة.",
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
