# extra_replies.py — أوامر إضافية:
#   1) "بوت" — البوت يعمل reply على رسالة المستخدم برد عشوائي بصيغة السوار.
#   2) "المالك" — يعرض صورة صاحب المجموعة + first_name (mention) + البايو
#                  + زر Online فيه الـ first_name برضو يحوّل على البروفايل عند الضغط.

import random
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from pyrogram.enums import ChatType, ChatMemberStatus
from driver.filters import command2, other_filters


# ─────────────────────────────────────────
# 1) أمر "بوت" — رد عشوائي بصيغة السوار
# ─────────────────────────────────────────

# الردود بصيغة السوار (نفس فكرة ╭───⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁───⟤)
SAWAR_REPLIES = [
    "**\n│  عاوز إيه يا قمر ؟\n**",
    "**\n│  نعم حبيبي قول\n**",
    "**\n│  انا تحت امرك\n**",
    "**\n│  ليه يا غالي\n**",
    "**\n│  ايوه قول كده\n**",
    "**\n│  حاضر يا باشا\n**",
    "**\n│  انا معاك قول\n**",
    "**\n│  ها عاوز اي\n**",
    "**\n│  اقولك على حاجة ؟\n**",
    "**\n│  انا سامعك يا حلو\n**",
    "**\n│  امرك يا كبير\n**",
    "**\n│  بقولك ايه ، احكي\n**",
]


@Client.on_message(command2(["بوت", "البوت"]) & other_filters)
async def bot_reply(_, message: Message):
    """لو حد كتب 'بوت' البوت بيعمل reply على رسالته برد عشوائي."""
    reply = random.choice(SAWAR_REPLIES)
    await message.reply_text(reply, quote=True)


# ─────────────────────────────────────────
# 2) أمر "المالك" — صورة صاحب المجموعة + بيانات + زر Online
# ─────────────────────────────────────────

async def _get_group_owner(client: Client, chat_id: int):
    """يرجع كائن المستخدم لصاحب المجموعة (creator)."""
    try:
        async for member in client.get_chat_members(
            chat_id, filter=__import__("pyrogram").enums.ChatMembersFilter.ADMINISTRATORS
        ):
            if member.status == ChatMemberStatus.OWNER:
                return member.user
    except Exception:
        # fallback — iterate all admins
        try:
            async for member in client.get_chat_members(chat_id):
                if member.status == ChatMemberStatus.OWNER:
                    return member.user
        except Exception:
            return None
    return None


@Client.on_message(command2(["المالك", "مالك", "صاحب المجموعه", "صاحب_المجموعه"]) & filters.group)
async def show_owner(client: Client, message: Message):
    """يعرض صورة صاحب المجموعة + first_name كـ منشن ماركداون + البايو + زر Online."""
    await message.delete()

    owner = await _get_group_owner(client, message.chat.id)
    if not owner:
        return await message.reply_text("**تعذر جلب بيانات صاحب المجموعة**")

    # جلب بيانات كاملة (البايو) — get_chat بـ user_id بيرجع ChatPreview/Chat فيها bio
    bio_text = ""
    try:
        full = await client.get_chat(owner.id)
        bio_text = getattr(full, "bio", "") or ""
    except Exception:
        bio_text = ""

    first_name = owner.first_name or "المالك"
    # منشن ماركداون
    mention = f"[{first_name}](tg://user?id={owner.id})"

    bio_line = f"**البايو:** `{bio_text}`" if bio_text else "**البايو:** `لا يوجد`"

    caption = (
        "**╭────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁────⟤**\n"
        f"**│ ** {mention}\n"
        f"**│ {bio_line}**\n"
        f"**│ ID:** `{owner.id}`\n"
        "**╰────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁────⟤**"
    )

    # زر Online فيه الـ first_name — لما يضغط عليه يحوّله للبروفايل
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🟢 {first_name}", url=f"tg://user?id={owner.id}")],
    ])

    # محاولة جلب أحدث صورة بروفايل وإرسالها مع الكابشن
    sent_photo = False
    try:
        async for photo in client.get_chat_photos(owner.id, limit=1):
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
        # مفيش صورة بروفايل أو الخصوصية مقفولة
        await message.reply_text(
            caption + "\n\n**ملاحظة:** لا توجد صورة بروفايل ظاهرة.",
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
