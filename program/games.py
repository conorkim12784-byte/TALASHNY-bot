"""
ألعاب تفاعلية للأعضاء (نسخة محدّثة):
- XO (إكس أو) مع نقاط (فوز=3 / تعادل=1)
- زواج بموافقة (مفيش اختيار عشوائي تلقائي)
- لعبة كت (Cat) — أسئلة عامة
- أمر "تاك" (مش لعبة) — تفعيل/تعطيل + صلاحية
- لعبة "تفكيك" — كلمة مبعثرة (نقاط)
- لعبة "تجميع" — حروف متفرقة لتكوين كلمة (نقاط)
- لعبة "قرعة" — يدخل أسماء والبوت يختار واحد
- نظام نقاط تراكمي عبر كل الجروبات + أمر "توب"
- تفعيل/تعطيل الألعاب لكل جروب: «تفعيل الالعاب» / «تعطيل الالعاب»

التخزين: ملف JSON محلي (games_data.json)
"""

import os
import re
import json
import random
import asyncio
from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from driver.filters import command2, other_filters
from driver.botadmin import is_master, has_permission
from config import SUDO_USERS

from program.games_words import SCRAMBLE_WORDS, BUILD_WORDS
from program.games_questions import CAT_QUESTIONS

DATA_FILE = "games_data.json"

# ═══════════════════════════════════════════════
# تخزين
# ═══════════════════════════════════════════════
def _load() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = {}
    d.setdefault("marriages", {})
    d.setdefault("tag_enabled", {})
    d.setdefault("games_enabled", {})   # {chat_id: bool}
    d.setdefault("scores", {})          # {user_id: {"name": str, "points": int}}
    return d


def _save(data: dict) -> None:
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _md_escape(name: str) -> str:
    return (name or "عضو").replace("[", "(").replace("]", ")")


def _mention(user) -> str:
    return f"[{_md_escape(user.first_name)}](tg://user?id={user.id})"


def _mention_id(uid: int, name: str) -> str:
    return f"[{_md_escape(name)}](tg://user?id={uid})"


# ═══════════════════════════════════════════════
# نظام النقاط (تراكمي عبر كل الجروبات)
# ═══════════════════════════════════════════════
def _add_points(user_id: int, first_name: str, points: int) -> int:
    data = _load()
    rec = data["scores"].get(str(user_id), {"name": first_name or "عضو", "points": 0})
    rec["name"] = first_name or rec.get("name") or "عضو"
    rec["points"] = int(rec.get("points", 0)) + int(points)
    data["scores"][str(user_id)] = rec
    _save(data)
    return rec["points"]


def _get_points(user_id: int) -> int:
    data = _load()
    return int(data["scores"].get(str(user_id), {}).get("points", 0))


# ═══════════════════════════════════════════════
# تفعيل/تعطيل الألعاب على مستوى الجروب
# ═══════════════════════════════════════════════
GAME_PERM = "tag"  # نفس صلاحية التاك تتحكم في تفعيل/تعطيل الألعاب


def _games_enabled(chat_id: int) -> bool:
    data = _load()
    val = data["games_enabled"].get(str(chat_id))
    return True if val is None else bool(val)


def _games_set(chat_id: int, value: bool) -> None:
    data = _load()
    data["games_enabled"][str(chat_id)] = bool(value)
    _save(data)


async def _can_manage(client: Client, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_USERS or is_master(user_id):
        return True
    if has_permission(chat_id, user_id, GAME_PERM):
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        status = getattr(member.status, "value", str(member.status)).lower()
        if status in ("creator", "owner", "administrator"):
            return True
    except Exception:
        pass
    return False


@Client.on_message(command2(["تفعيل الالعاب", "تفعيل الألعاب"]) & other_filters)
async def games_enable(client: Client, message: Message):
    if not message.from_user:
        return
    if not await _can_manage(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ مش عندك صلاحية")
    _games_set(message.chat.id, True)
    await message.reply("✔ **تم تفعيل الألعاب** 🎮")


@Client.on_message(command2(["تعطيل الالعاب", "تعطيل الألعاب", "ايقاف الالعاب"]) & other_filters)
async def games_disable(client: Client, message: Message):
    if not message.from_user:
        return
    if not await _can_manage(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ مش عندك صلاحية")
    _games_set(message.chat.id, False)
    await message.reply("✘ **تم تعطيل الألعاب**")


def _games_ok(message: Message) -> bool:
    return _games_enabled(message.chat.id)


# ═══════════════════════════════════════════════
# اختيار عضو عشوائي
# ═══════════════════════════════════════════════
async def _random_member(client: Client, chat_id: int, exclude_ids: set):
    try:
        candidates = []
        async for m in client.get_chat_members(chat_id):
            u = m.user
            if not u or u.is_bot:
                continue
            if u.id in exclude_ids:
                continue
            candidates.append(u)
            if len(candidates) >= 200:
                break
        if not candidates:
            return None
        return random.choice(candidates)
    except Exception:
        return None


# ═══════════════════════════════════════════════
# 💍 نظام الزواج — بموافقة فقط
# ═══════════════════════════════════════════════
def _get_spouse(chat_id: int, user_id: int) -> Optional[dict]:
    data = _load()
    return data["marriages"].get(str(chat_id), {}).get(str(user_id))


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
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        return None
    arg = parts[1].strip()
    if message.entities:
        for ent in message.entities:
            if ent.type.value == "text_mention" and ent.user:
                return ent.user
    arg = arg.lstrip("@")
    try:
        return await client.get_users(arg)
    except Exception:
        return None


@Client.on_message(command2(["زوجني", "اتجوز"]) & other_filters)
async def marry_cmd(client: Client, message: Message):
    if not message.from_user or not _games_ok(message):
        return
    proposer = message.from_user
    chat_id = message.chat.id
    target = await _resolve_target(client, message)

    if not target:
        return await message.reply(
            "✦ لازم تحدد الشخص اللي عايز تتجوزه — رد على رسالته أو اعمله منشن.\n"
            "مثال: `زوجني @username`"
        )

    if target.is_bot:
        return await message.reply("✦ مينفعش تتجوز بوت 🤖")
    if target.id == proposer.id:
        return await message.reply("✦ مينفعش تتجوز نفسك 😅")
    if _get_spouse(chat_id, proposer.id):
        return await message.reply("✦ انت متجوز بالفعل، لازم تطلق الأول 💔")
    if _get_spouse(chat_id, target.id):
        return await message.reply(f"✦ {_mention(target)} متجوز بالفعل 💔")

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
    proposer_id = int(proposer_id); target_id = int(target_id)
    if query.from_user.id != target_id:
        return await query.answer("✦ القرار ليك انت بس", show_alert=True)
    chat_id = query.message.chat.id
    if answer == "n":
        await query.message.edit_text(f"💔 {_mention(query.from_user)} رفض/رفضت عرض الزواج")
        return await query.answer("تم الرفض")
    if _get_spouse(chat_id, proposer_id) or _get_spouse(chat_id, target_id):
        await query.message.edit_text("✦ العرض اتلغى — أحد الطرفين بقى متجوز")
        return await query.answer()
    try:
        proposer = await client.get_users(proposer_id)
    except Exception:
        return await query.answer("تعذر جلب بيانات العريس", show_alert=True)
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


@Client.on_message(command2(["زوجي", "زوجتي"]) & other_filters)
async def my_spouse(client: Client, message: Message):
    if not message.from_user or not _games_ok(message):
        return
    rec = _get_spouse(message.chat.id, message.from_user.id)
    if not rec:
        return await message.reply("✦ انت لسه أعزب/عزباء 😅 جرب: `زوجني @user`")
    await message.reply(
        f"💍 {_mention(message.from_user)} متجوز/متجوزة من "
        f"{_mention_id(rec['id'], rec['name'])}"
    )


@Client.on_message(command2(["طلاق", "طلق"]) & other_filters)
async def divorce_cmd(client: Client, message: Message):
    if not message.from_user or not _games_ok(message):
        return
    rec = _remove_marriage(message.chat.id, message.from_user.id)
    if not rec:
        return await message.reply("✦ انت أصلًا مش متجوز 😅")
    await message.reply(
        f"💔 {_mention(message.from_user)} طلق/طلقت "
        f"{_mention_id(rec['id'], rec['name'])}\nالله يعوض على الكل 🥲"
    )


# ═══════════════════════════════════════════════
# ❌⭕ لعبة XO + نقاط (فوز=3، تعادل=1)
# ═══════════════════════════════════════════════
games_xo: dict = {}
WIN_LINES = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]

XO_WIN_POINTS = 3
XO_DRAW_POINTS = 1


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


def _xo_join_keyboard(msg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("انضمام ➕", callback_data=f"xo:j:{msg_id}:0")],
        [InlineKeyboardButton("إلغاء ❌", callback_data=f"xo:c:{msg_id}:0")],
    ])


def _xo_check(board: list) -> Optional[str]:
    for a, b, c in WIN_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if all(board):
        return "draw"
    return None


@Client.on_message(command2(["xo", "اكس اوه", "إكس", "إكسأو", "اكسأو", "اكس او", "اكس"]) & other_filters)
async def xo_start(client: Client, message: Message):
    if not message.from_user or not _games_ok(message):
        return
    target = await _resolve_target(client, message)
    if not target:
        sent = await message.reply(
            f"❌⭕ **لعبة XO**\n\n"
            f"اللاعب: {_mention(message.from_user)}\n\n"
            f"اضغط «انضمام» عشان تلعب ضده.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("جاري التحميل...", callback_data="xo:noop")]]),
        )
        games_xo[sent.id] = {
            "waiting": True,
            "p1": {"id": message.from_user.id, "name": message.from_user.first_name or "X"},
        }
        await sent.edit_reply_markup(reply_markup=_xo_join_keyboard(sent.id))
        return
    if target.is_bot or target.id == message.from_user.id:
        return await message.reply("✦ مينفعش تلعب مع نفسك أو مع بوت")
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


@Client.on_callback_query(filters.regex(r"^xo:(m|c|j):(\d+):(\d+)$"))
async def xo_cb(client: Client, query: CallbackQuery):
    action, msg_id, idx = query.data.split(":")[1:]
    msg_id = int(msg_id); idx = int(idx)
    game = games_xo.get(msg_id)
    if not game:
        return await query.answer("✦ اللعبة انتهت أو مش موجودة", show_alert=True)
    uid = query.from_user.id

    if action == "j":
        if not game.get("waiting"):
            return await query.answer("✦ اللعبة بدأت بالفعل", show_alert=True)
        if uid == game["p1"]["id"]:
            return await query.answer("✦ مينفعش تنضم لنفسك 😅", show_alert=True)
        if query.from_user.is_bot:
            return await query.answer("✦ مفيش بوتات هنا", show_alert=True)
        game["p2"] = {"id": uid, "name": query.from_user.first_name or "O"}
        game["board"] = [None] * 9
        game["turn"] = game["p1"]["id"]
        game["waiting"] = False
        await query.message.edit_text(
            f"❌⭕ لعبة XO\n\n"
            f"❌ {_mention_id(game['p1']['id'], game['p1']['name'])}\n"
            f"⭕ {_mention_id(game['p2']['id'], game['p2']['name'])}\n\n"
            f"الدور على: ❌ {_mention_id(game['p1']['id'], game['p1']['name'])}",
            reply_markup=_xo_keyboard(msg_id, game["board"]),
        )
        return await query.answer("تم الانضمام 🎮")

    if action == "c":
        owners = {game["p1"]["id"]}
        if game.get("p2"):
            owners.add(game["p2"]["id"])
        if uid not in owners:
            return await query.answer("✦ مش بتاعتك", show_alert=True)
        games_xo.pop(msg_id, None)
        await query.message.edit_text(f"❌ تم إلغاء اللعبة بواسطة {_mention(query.from_user)}")
        return await query.answer("تم الإلغاء")

    if game.get("waiting"):
        return await query.answer("✦ اللعبة لسه ماتبدأتش", show_alert=True)
    if uid not in (game["p1"]["id"], game["p2"]["id"]):
        return await query.answer("✦ اللعبة دي مش ليك", show_alert=True)
    if uid != game["turn"]:
        return await query.answer("✦ مش دورك", show_alert=True)
    if game["board"][idx] is not None:
        return await query.answer("✦ المربع ده محجوز", show_alert=True)

    symbol = "❌" if uid == game["p1"]["id"] else "⭕"
    game["board"][idx] = symbol
    result = _xo_check(game["board"])
    if result:
        games_xo.pop(msg_id, None)
        if result == "draw":
            _add_points(game["p1"]["id"], game["p1"]["name"], XO_DRAW_POINTS)
            _add_points(game["p2"]["id"], game["p2"]["name"], XO_DRAW_POINTS)
            await query.message.edit_text(
                f"🤝 تعادل! (+{XO_DRAW_POINTS} لكل لاعب)\n\n"
                f"❌ {_mention_id(game['p1']['id'], game['p1']['name'])}\n"
                f"⭕ {_mention_id(game['p2']['id'], game['p2']['name'])}",
            )
        else:
            winner = game["p1"] if result == "❌" else game["p2"]
            loser = game["p2"] if result == "❌" else game["p1"]
            total = _add_points(winner["id"], winner["name"], XO_WIN_POINTS)
            await query.message.edit_text(
                f"🏆 فاز {result} {_mention_id(winner['id'], winner['name'])} (+{XO_WIN_POINTS})\n"
                f"💔 خسر {_mention_id(loser['id'], loser['name'])}\n"
                f"⭐ نقاطه الكلية: {total}"
            )
        return await query.answer("انتهت اللعبة")

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


@Client.on_callback_query(filters.regex(r"^xo:noop$"))
async def xo_noop(client: Client, query: CallbackQuery):
    await query.answer()


# ═══════════════════════════════════════════════
# 🐱 لعبة كت — أسئلة عامة
# ═══════════════════════════════════════════════
@Client.on_message(command2(["كت", "cat", "لعبة كت", "تويت"]) & other_filters)
async def cat_game(client: Client, message: Message):
    if not message.from_user or not _games_ok(message):
        return
    q = random.choice(CAT_QUESTIONS)
    await message.reply(
        f"🎲 **لعبة كت**\n\n"
        f"{_mention(message.from_user)} خد سؤالك:\n\n"
        f"**{q}**"
    )


# ═══════════════════════════════════════════════
# 🔤 لعبة تفكيك — كلمة مبعثرة
# 🧩 لعبة تجميع — حروف متفرقة لتكوين كلمة
# نقاط: تفكيك = 5 / تجميع = 5
# ═══════════════════════════════════════════════
WORD_GAME_TIMEOUT = 60  # ثانية
WORD_WIN_POINTS = 5

# {chat_id: {"word": str, "shuffled": str, "starter_id": int, "msg_id": int, "kind": "tafkeek"|"tagmee3"}}
active_word_games: dict = {}


def _shuffle_word(w: str) -> str:
    chars = list(w)
    for _ in range(20):
        random.shuffle(chars)
        if "".join(chars) != w:
            break
    return "".join(chars)


def _spaced_letters(w: str) -> str:
    chars = list(w)
    random.shuffle(chars)
    return " - ".join(chars)


async def _start_word_game(message: Message, kind: str):
    chat_id = message.chat.id
    if chat_id in active_word_games:
        return await message.reply("✦ في لعبة كلمات شغالة دلوقتي، استنى تخلص.")
    pool = SCRAMBLE_WORDS if kind == "tafkeek" else BUILD_WORDS
    word = random.choice(pool)
    if kind == "tafkeek":
        display = _shuffle_word(word)
        title = "🔤 **لعبة تفكيك**"
        hint = f"رتّب الحروف وكوّن الكلمة الأصلية:\n\n`{display}`"
    else:
        display = _spaced_letters(word)
        title = "🧩 **لعبة تجميع**"
        hint = f"جمّع الحروف دي وكوّن كلمة:\n\n`{display}`"
    sent = await message.reply(
        f"{title}\n\n{hint}\n\n"
        f"⏱ عندك {WORD_GAME_TIMEOUT} ثانية — اكتب الإجابة في الجروب.\n"
        f"🏆 الجائزة: +{WORD_WIN_POINTS} نقاط"
    )
    active_word_games[chat_id] = {
        "word": word, "shuffled": display, "starter_id": message.from_user.id,
        "msg_id": sent.id, "kind": kind,
    }
    await asyncio.sleep(WORD_GAME_TIMEOUT)
    state = active_word_games.get(chat_id)
    if state and state["msg_id"] == sent.id:
        active_word_games.pop(chat_id, None)
        try:
            await message.reply(f"⌛ خلص الوقت! الكلمة كانت: **{word}**")
        except Exception:
            pass


@Client.on_message(command2(["تفكيك", "تفكيك كلمة"]) & other_filters)
async def tafkeek_cmd(client: Client, message: Message):
    if not message.from_user or not _games_ok(message):
        return
    await _start_word_game(message, "tafkeek")


@Client.on_message(command2(["تجميع", "تجميع كلمة"]) & other_filters)
async def tagmee3_cmd(client: Client, message: Message):
    if not message.from_user or not _games_ok(message):
        return
    await _start_word_game(message, "tagmee3")


# مستمع للإجابات
@Client.on_message(filters.group & filters.text & ~filters.via_bot, group=15)
async def word_answer_listener(client: Client, message: Message):
    if not message.from_user or message.from_user.is_bot:
        return
    state = active_word_games.get(message.chat.id)
    if not state:
        return
    text = (message.text or "").strip()
    if not text or text.startswith("/"):
        return
    # نقارن بدون تشكيل/مسافات
    norm = re.sub(r"\s+", "", text)
    if norm == state["word"]:
        active_word_games.pop(message.chat.id, None)
        total = _add_points(message.from_user.id, message.from_user.first_name or "عضو", WORD_WIN_POINTS)
        await message.reply(
            f"🎉 إجابة صح يا {_mention(message.from_user)}!\n"
            f"الكلمة: **{state['word']}**\n"
            f"+{WORD_WIN_POINTS} نقاط — مجموعك: {total} ⭐"
        )


# ═══════════════════════════════════════════════
# 🎯 لعبة قرعة — يدخل أسماء والبوت يختار واحد
# الاستخدام:
#   قرعة محمد، أحمد، علي
#   قرعة محمد - أحمد - علي
# ═══════════════════════════════════════════════
@Client.on_message(command2(["قرعة", "قرعه"]) & other_filters)
async def qor3a_cmd(client: Client, message: Message):
    if not message.from_user or not _games_ok(message):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply(
            "✦ اكتب الأسماء بعد الأمر.\n"
            "مثال: `قرعة محمد، أحمد، علي`"
        )
    raw = parts[1]
    names = [n.strip() for n in re.split(r"[،,\-\n]+", raw) if n.strip()]
    if len(names) < 2:
        return await message.reply("✦ لازم اسمين على الأقل.")
    pick = random.choice(names)
    pretty = "\n".join(f"• {n}" for n in names)
    await message.reply(
        f"🎯 **القرعة**\n\n{pretty}\n\n"
        f"🥁 ...\n\n"
        f"🏆 الفايز هو: **{pick}**"
    )


# ═══════════════════════════════════════════════
# 🏆 توب النقاط
# ═══════════════════════════════════════════════
@Client.on_message(command2(["توب", "توب النقاط", "top", "ترتيب"]) & other_filters)
async def top_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    data = _load()
    items = list(data.get("scores", {}).items())
    if not items:
        return await message.reply("✦ لسه مفيش نقاط — العب شويه الأول 😄")
    items.sort(key=lambda kv: int(kv[1].get("points", 0)), reverse=True)
    top = items[:10]
    lines = ["🏆 **توب النقاط (تراكمي)**\n"]
    medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
    for i, (uid, rec) in enumerate(top):
        lines.append(f"{medals[i]} {_md_escape(rec.get('name','عضو'))} — {rec.get('points',0)}")
    me = data.get("scores", {}).get(str(message.from_user.id))
    if me:
        rank = next((i + 1 for i, (uid, _) in enumerate(items) if uid == str(message.from_user.id)), None)
        lines.append(f"\n👤 ترتيبك: #{rank} — نقاطك: {me.get('points',0)}")
    await message.reply("\n".join(lines))


@Client.on_message(command2(["نقاطي", "نقطي"]) & other_filters)
async def my_points(client: Client, message: Message):
    if not message.from_user:
        return
    p = _get_points(message.from_user.id)
    await message.reply(f"⭐ نقاطك: **{p}**")


# ═══════════════════════════════════════════════
# 🏷️ أمر التاك (Tag) — مش لعبة
# ═══════════════════════════════════════════════
TAG_PERM = "tag"


def _tag_is_enabled(chat_id: int) -> bool:
    data = _load()
    val = data.get("tag_enabled", {}).get(str(chat_id))
    return True if val is None else bool(val)


def _tag_set(chat_id: int, value: bool) -> None:
    data = _load()
    data.setdefault("tag_enabled", {})[str(chat_id)] = bool(value)
    _save(data)


async def _can_use_tag(client: Client, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_USERS or is_master(user_id):
        return True
    if has_permission(chat_id, user_id, TAG_PERM):
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        status = getattr(member.status, "value", str(member.status)).lower()
        if status in ("creator", "owner"):
            return True
    except Exception:
        pass
    return False


@Client.on_message(command2(["تفعيل التاك", "تفعيل تاك"]) & other_filters)
async def tag_enable(client: Client, message: Message):
    if not message.from_user:
        return
    if not await _can_use_tag(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ مش عندك صلاحية تتحكم في التاك")
    _tag_set(message.chat.id, True)
    await message.reply("✔ **تم تفعيل أمر التاك** 🏷️")


@Client.on_message(command2(["تعطيل التاك", "تعطيل تاك", "ايقاف التاك"]) & other_filters)
async def tag_disable(client: Client, message: Message):
    if not message.from_user:
        return
    if not await _can_use_tag(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ مش عندك صلاحية تتحكم في التاك")
    _tag_set(message.chat.id, False)
    await message.reply("✘ **تم تعطيل أمر التاك**")


@Client.on_message(command2(["تاك", "tag", "منشن"]) & other_filters)
async def tag_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    chat_id = message.chat.id
    if not await _can_use_tag(client, chat_id, message.from_user.id):
        return await message.reply(
            "❌ أمر التاك للمالك / أصحاب البوت / مدير الجروب / مدير البوت بصلاحية «التاك»"
        )
    if not _tag_is_enabled(chat_id):
        return await message.reply("✘ أمر التاك معطّل في الجروب — فعّله بـ `تفعيل التاك`")

    parts = (message.text or "").split(maxsplit=2)
    count: Optional[int] = None
    note = ""
    if len(parts) >= 2:
        a = parts[1].strip()
        if a.isdigit():
            count = max(1, min(int(a), 200))
            if len(parts) >= 3:
                note = parts[2].strip()
        elif a in ("الكل", "all"):
            count = None
            if len(parts) >= 3:
                note = parts[2].strip()
        else:
            note = (message.text.split(maxsplit=1)[1]).strip()

    members = []
    try:
        async for m in client.get_chat_members(chat_id):
            u = m.user
            if not u or u.is_bot:
                continue
            members.append(u)
            if count is None:
                if len(members) >= 500:
                    break
            else:
                if len(members) >= count + 5:
                    break
    except Exception as e:
        return await message.reply(f"✘ تعذر جلب الأعضاء: {e}")

    if not members:
        return await message.reply("✘ مفيش أعضاء للتاك")
    if count is not None:
        members = members[:count]

    header = f"🏷️ **تاك ({len(members)})**" + (f"\n📝 {note}" if note else "") + "\n\n"
    chunk = []; chunk_len = 0; sent_first = False

    async def flush():
        nonlocal sent_first, chunk, chunk_len
        if not chunk:
            return
        text = (header if not sent_first else "") + " ".join(chunk)
        try:
            await client.send_message(chat_id, text, disable_web_page_preview=True)
        except Exception:
            pass
        sent_first = True
        chunk = []; chunk_len = 0
        await asyncio.sleep(0.4)

    for u in members:
        m = _mention(u)
        if chunk_len + len(m) + 1 > 3500:
            await flush()
        chunk.append(m)
        chunk_len += len(m) + 1
    await flush()
