"""
ألعاب تفاعلية للأعضاء:
- لعبة XO (إكس أو) — لاعبين بأزرار Inline
- نظام الزواج: زوجني / زوجي / طلاق
التخزين: ملف JSON محلي (games_data.json)
"""

import os
import json
import random
from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from driver.filters import command2, other_filters

DATA_FILE = "games_data.json"

# ═══════════════════════════════════════════════
# تخزين
# ═══════════════════════════════════════════════
def _load() -> dict:
    if not os.path.exists(DATA_FILE):
        return {"marriages": {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            d.setdefault("marriages", {})
            return d
    except Exception:
        return {"marriages": {}}


def _save(data: dict) -> None:
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _mention(user) -> str:
    name = (user.first_name or "عضو").replace("[", "(").replace("]", ")")
    return f"[{name}](tg://user?id={user.id})"


def _mention_id(uid: int, name: str) -> str:
    name = (name or "عضو").replace("[", "(").replace("]", ")")
    return f"[{name}](tg://user?id={uid})"


# ═══════════════════════════════════════════════
# 💍 نظام الزواج
# ═══════════════════════════════════════════════
def _get_spouse(chat_id: int, user_id: int) -> Optional[dict]:
    data = _load()
    chat = data["marriages"].get(str(chat_id), {})
    rec = chat.get(str(user_id))
    return rec


def _set_marriage(chat_id: int, u1: dict, u2: dict) -> None:
    data = _load()
    chat = data["marriages"].setdefault(str(chat_id), {})
    chat[str(u1["id"])] = {"id": u2["id"], "name": u2["name"]}
    chat[str(u2["id"])] = {"id": u1["id"], "name": u1["name"]}
    _save(data)


def _remove_marriage(chat_id: int, user_id: int) -> Optional[dict]:
    data = _load()
    chat = data["marriages"].get(str(chat_id), {})
    rec = chat.pop(str(user_id), None)
    if rec:
        chat.pop(str(rec["id"]), None)
        _save(data)
    return rec


async def _resolve_target(client: Client, message: Message):
    """جيب اليوزر الهدف من الرد أو المنشن أو اليوزرنيم"""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        return None

    arg = parts[1].strip()
    # entity mention
    if message.entities:
        for ent in message.entities:
            if ent.type.value == "text_mention" and ent.user:
                return ent.user

    arg = arg.lstrip("@")
    try:
        return await client.get_users(arg)
    except Exception:
        return None


# ── زوجني ──
@Client.on_message(command2(["زوجني", "اتجوز"]) & other_filters)
async def marry_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    proposer = message.from_user

    target = await _resolve_target(client, message)
    if not target:
        await message.reply("✦ اعمل ريبلاي على الشخص أو اكتب يوزره\nمثال: `زوجني @user`")
        return

    if target.is_bot:
        await message.reply("✦ مينفعش تتجوز بوت 🤖")
        return

    if target.id == proposer.id:
        await message.reply("✦ مينفعش تتجوز نفسك 😅")
        return

    chat_id = message.chat.id
    if _get_spouse(chat_id, proposer.id):
        await message.reply("✦ انت متجوز بالفعل، لازم تطلق الأول 💔")
        return
    if _get_spouse(chat_id, target.id):
        await message.reply(f"✦ {_mention(target)} متجوز بالفعل 💔")
        return

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("موافق ✅", callback_data=f"mrg:y:{proposer.id}:{target.id}"),
        InlineKeyboardButton("رفض ❌", callback_data=f"mrg:n:{proposer.id}:{target.id}"),
    ]])
    await message.reply(
        f"💍 {_mention(proposer)} عرض الزواج على {_mention(target)}\n\n"
        f"يا {target.first_name}، توافقي/توافق؟",
        reply_markup=kb,
    )


@Client.on_callback_query(filters.regex(r"^mrg:(y|n):(\d+):(\d+)$"))
async def marry_cb(client: Client, query: CallbackQuery):
    answer, proposer_id, target_id = query.data.split(":")[1:]
    proposer_id = int(proposer_id)
    target_id = int(target_id)

    if query.from_user.id != target_id:
        await query.answer("✦ القرار ليك انت بس مش لحد تاني", show_alert=True)
        return

    chat_id = query.message.chat.id

    if answer == "n":
        await query.message.edit_text(
            f"💔 {_mention(query.from_user)} رفض/رفضت عرض الزواج"
        )
        await query.answer("تم الرفض")
        return

    # موافقة — تأكد إن ولا واحد فيهم اتجوز في الفترة دي
    if _get_spouse(chat_id, proposer_id) or _get_spouse(chat_id, target_id):
        await query.message.edit_text("✦ العرض اتلغى — أحد الطرفين بقى متجوز")
        await query.answer()
        return

    try:
        proposer = await client.get_users(proposer_id)
    except Exception:
        await query.answer("تعذر جلب بيانات العريس", show_alert=True)
        return

    _set_marriage(
        chat_id,
        {"id": proposer.id, "name": proposer.first_name or "عضو"},
        {"id": query.from_user.id, "name": query.from_user.first_name or "عضو"},
    )

    await query.message.edit_text(
        f"💞 مبروك الزواج 🎉🎊\n\n"
        f"العريس: {_mention(proposer)}\n"
        f"العروسة: {_mention(query.from_user)}\n\n"
        f"عقبال ما نشوف الاولاد ✨"
    )
    await query.answer("تم الزواج 💍")


# ── زوجي ──
@Client.on_message(command2(["زوجي", "زوجتي"]) & other_filters)
async def my_spouse(client: Client, message: Message):
    if not message.from_user:
        return
    rec = _get_spouse(message.chat.id, message.from_user.id)
    if not rec:
        await message.reply("✦ انت لسه أعزب/عزباء 😅 جرب: `زوجني @user`")
        return
    await message.reply(
        f"💍 {_mention(message.from_user)} متجوز/متجوزة من "
        f"{_mention_id(rec['id'], rec['name'])}"
    )


# ── طلاق ──
@Client.on_message(command2(["طلاق", "طلق"]) & other_filters)
async def divorce_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    rec = _remove_marriage(message.chat.id, message.from_user.id)
    if not rec:
        await message.reply("✦ انت أصلًا مش متجوز 😅")
        return
    await message.reply(
        f"💔 {_mention(message.from_user)} طلق/طلقت "
        f"{_mention_id(rec['id'], rec['name'])}\nالله يعوض على الكل 🥲"
    )


# ═══════════════════════════════════════════════
# ❌⭕ لعبة XO
# ═══════════════════════════════════════════════
# games_xo[message_id] = {"board":[...], "turn":id, "p1":{id,name}, "p2":{id,name}}
games_xo: dict = {}

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
]


def _xo_keyboard(msg_id: int, board: list) -> InlineKeyboardMarkup:
    rows = []
    for r in range(3):
        row = []
        for c in range(3):
            i = r * 3 + c
            cell = board[i] or "·"
            row.append(InlineKeyboardButton(cell, callback_data=f"xo:m:{msg_id}:{i}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("إلغاء اللعبة ❌", callback_data=f"xo:c:{msg_id}:0")])
    return InlineKeyboardMarkup(rows)


def _xo_check(board: list) -> Optional[str]:
    for a, b, c in WIN_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if all(board):
        return "draw"
    return None


@Client.on_message(command2(["xo", "اكس اوه", "إكس", "إكسأو", "اكسأو"]) & other_filters)
async def xo_start(client: Client, message: Message):
    if not message.from_user:
        return
    target = await _resolve_target(client, message)
    if not target:
        await message.reply("✦ اعمل ريبلاي على الخصم أو اكتب يوزره\nمثال: `xo @user`")
        return
    if target.is_bot or target.id == message.from_user.id:
        await message.reply("✦ مينفعش تلعب مع نفسك أو مع بوت")
        return

    sent = await message.reply(
        f"❌⭕ لعبة XO\n\n"
        f"❌ {_mention(message.from_user)}\n"
        f"⭕ {_mention(target)}\n\n"
        f"الدور على: {_mention(message.from_user)}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("جاري التحميل...", callback_data="xo:noop")]]),
    )
    games_xo[sent.id] = {
        "board": [None] * 9,
        "turn": message.from_user.id,
        "p1": {"id": message.from_user.id, "name": message.from_user.first_name or "X"},
        "p2": {"id": target.id, "name": target.first_name or "O"},
    }
    await sent.edit_reply_markup(reply_markup=_xo_keyboard(sent.id, games_xo[sent.id]["board"]))


@Client.on_callback_query(filters.regex(r"^xo:(m|c):(\d+):(\d+)$"))
async def xo_cb(client: Client, query: CallbackQuery):
    action, msg_id, idx = query.data.split(":")[1:]
    msg_id = int(msg_id)
    idx = int(idx)
    game = games_xo.get(msg_id)
    if not game:
        await query.answer("✦ اللعبة انتهت أو مش موجودة", show_alert=True)
        return

    uid = query.from_user.id
    if uid not in (game["p1"]["id"], game["p2"]["id"]):
        await query.answer("✦ اللعبة دي مش ليك", show_alert=True)
        return

    if action == "c":
        games_xo.pop(msg_id, None)
        await query.message.edit_text(
            f"❌ تم إلغاء اللعبة بواسطة {_mention(query.from_user)}"
        )
        await query.answer("تم الإلغاء")
        return

    if uid != game["turn"]:
        await query.answer("✦ مش دورك", show_alert=True)
        return

    if game["board"][idx] is not None:
        await query.answer("✦ المربع ده محجوز", show_alert=True)
        return

    symbol = "❌" if uid == game["p1"]["id"] else "⭕"
    game["board"][idx] = symbol

    result = _xo_check(game["board"])
    if result:
        games_xo.pop(msg_id, None)
        if result == "draw":
            await query.message.edit_text(
                f"🤝 تعادل!\n\n❌ {_mention_id(game['p1']['id'], game['p1']['name'])}\n"
                f"⭕ {_mention_id(game['p2']['id'], game['p2']['name'])}",
                reply_markup=InlineKeyboardMarkup([_render_final(game['board'])]) if False else None,
            )
        else:
            winner = game["p1"] if result == "❌" else game["p2"]
            loser = game["p2"] if result == "❌" else game["p1"]
            await query.message.edit_text(
                f"🏆 فاز {result} {_mention_id(winner['id'], winner['name'])}\n"
                f"💔 خسر {_mention_id(loser['id'], loser['name'])}"
            )
        await query.answer("انتهت اللعبة")
        return

    # تبديل الدور
    game["turn"] = game["p2"]["id"] if uid == game["p1"]["id"] else game["p1"]["id"]
    next_name = game["p2"]["name"] if game["turn"] == game["p2"]["id"] else game["p1"]["name"]
    next_sym = "⭕" if game["turn"] == game["p2"]["id"] else "❌"

    await query.message.edit_text(
        f"❌⭕ لعبة XO\n\n"
        f"❌ {_mention_id(game['p1']['id'], game['p1']['name'])}\n"
        f"⭕ {_mention_id(game['p2']['id'], game['p2']['name'])}\n\n"
        f"الدور على: {next_sym} {_mention_id(game['turn'], next_name)}",
        reply_markup=_xo_keyboard(msg_id, game["board"]),
    )
    await query.answer()


def _render_final(board):
    return [InlineKeyboardButton(c or "·", callback_data="xo:noop") for c in board[:3]]


@Client.on_callback_query(filters.regex(r"^xo:noop$"))
async def xo_noop(client: Client, query: CallbackQuery):
    await query.answer()
