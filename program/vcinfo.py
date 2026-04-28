# vcinfo.py — مين في الكول + مين مشغّل الأغنية
#
# السلوك المطلوب:
#  • "مين في الكول": لو المساعد فعلاً في الكول → يجيب القائمة من الكول مباشرة.
#    لو مش في الكول → يدخل بصمت (بدون تشغيل) عشان يقرأ القائمة، ثم يطلع.
#    لا يؤثر إطلاقاً على الأغنية الشغالة أو التشغيل العادي.
#  • "مين مشغل": يجيب من طلب الأغنية الحالية (current_requester).

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.raw import functions as raw_functions, types as raw_types
from driver.filters import command, command2, other_filters
from driver.queues import QUEUE
from driver.nowplaying import current_requester
from driver.veez import call_py, user


# ─────────────────────────────────────────
# مساعد: هل المساعد فعلاً متصل بالكول دلوقتي عبر py-tgcalls؟
# ─────────────────────────────────────────
def _userbot_is_in_call(chat_id: int) -> bool:
    try:
        # py-tgcalls يحتفظ بقائمة المكالمات النشطة
        calls = getattr(call_py, "calls", None)
        if calls and chat_id in calls:
            return True
    except Exception:
        pass
    return False


# ─────────────────────────────────────────
# جلب المشتركين عبر raw API بدون الحاجة لتشغيل الكول
# ─────────────────────────────────────────
async def _get_call_participants_raw(chat_id: int):
    """يرجع list من user_id للمشتركين في الكول، أو None لو مفيش كول."""
    try:
        peer = await user.resolve_peer(chat_id)
        full = await user.invoke(
            raw_functions.channels.GetFullChannel(channel=peer)
        ) if isinstance(peer, raw_types.InputPeerChannel) else await user.invoke(
            raw_functions.messages.GetFullChat(chat_id=peer.chat_id)
        )
        gc = getattr(full.full_chat, "call", None)
        if not gc:
            return None  # مفيش كول نشطة
        gc_input = raw_types.InputGroupCall(id=gc.id, access_hash=gc.access_hash)
        res = await user.invoke(
            raw_functions.phone.GetGroupParticipants(
                call=gc_input,
                ids=[],
                sources=[],
                offset="",
                limit=200,
            )
        )
        out = []
        for p in res.participants:
            uid = None
            peer_obj = getattr(p, "peer", None)
            if isinstance(peer_obj, raw_types.PeerUser):
                uid = peer_obj.user_id
            if uid:
                out.append(uid)
        return out
    except Exception:
        return None


# ─────────────────────────────────────────
# أمر: مين في الكول
# ─────────────────────────────────────────
@Client.on_message(
    (command(["incall"]) | command2(["في_الكول", "الكول", "كول", "في الكول", "مين_في_الكول", "مين في الكول"]))
    & other_filters
)
async def who_in_call(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id

    # نقرأ القائمة عبر raw API — لا نلمس التشغيل ولا ندخل/نطلع من الكول
    user_ids = await _get_call_participants_raw(chat_id)

    if user_ids is None:
        return await m.reply("🎙 **لا توجد دردشة صوتية نشطة في المجموعة**")

    if not user_ids:
        return await m.reply("🎙 **الكول فارغة حالياً**")

    members = []
    for uid in user_ids:
        try:
            u = await c.get_users(uid)
            if u.is_bot:
                continue
            name = u.first_name or "مجهول"
            members.append(f"[{name}](tg://user?id={uid})")
        except Exception:
            continue

    if not members:
        return await m.reply("🎙 **الكول فارغة حالياً**")

    members_text = "\n".join(f"  {i+1}. {u}" for i, u in enumerate(members))
    await m.reply(
        f"🎙 **المتواجدون في الكول**\n"
        f"**العدد:** `{len(members)}`\n\n"
        f"{members_text}"
    )


# ─────────────────────────────────────────
# أمر: مين مشغّل
# ─────────────────────────────────────────
@Client.on_message(
    (command(["nowplaying", "np"]) | command2(["مشغّل", "مشغل", "الان", "مين_مشغل", "مين مشغل"]))
    & other_filters
)
async def now_playing(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id

    if chat_id not in QUEUE or not QUEUE[chat_id]:
        return await m.reply("**مـفـيش حـاجه شـغاله**")

    current = QUEUE[chat_id][0]
    songname = current[0]
    media_type = current[3]

    requester = current_requester.get(chat_id)
    if requester:
        req_text = f"**طُلبت بواسطة:** [{requester['first_name']}](tg://user?id={requester['user_id']})"
    else:
        req_text = "**طُلبت بواسطة:** `غير معروف`"

    type_icon = "🎬" if media_type == "Video" else "🎶"
    type_text = "فيديو" if media_type == "Video" else "صوت"

    queue_size = len(QUEUE[chat_id])
    queue_text = f"\n📋 **في الانتظار:** `{queue_size - 1}` مقطع" if queue_size > 1 else ""

    await m.reply(
        f"{type_icon} **شغال الآن**\n\n"
        f"**الاسم:** `{songname}`\n"
        f"**النوع:** `{type_text}`\n"
        f"{req_text}"
        f"{queue_text}"
    )
