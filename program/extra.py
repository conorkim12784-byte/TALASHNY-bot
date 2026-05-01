"""broadcast — نظام إذاعة محسن (يستخدم البوت نفسه عبر served chats من DB).

الميزات:
- `اذاعه` / `اذاعة` / `gcast` — إرسال نص أو رد على رسالة لكل الجروبات.
- `ذت` / `اذت` / `اذع` — إذاعة + تثبيت تلقائي.
- `اذاعه فوروورد` — Forward بدل send.
- شريط تقدّم حي + ملخص نهائي مفصّل.
- تخطّي الجروبات اللي مفيش صلاحيات أو محظور فيها بشكل آمن.
- صلاحية: SUDO_USERS فقط.

ملحوظة: الملف ده بيستبدل program/broadcast.py القديم (اللي كان بيستخدم
حساب Anonymous وبيلف على dialogs بحساب يوزر). النظام الجديد أسرع وأدق.
"""
import asyncio
import time
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import (
    FloodWait,
    ChatWriteForbidden,
    UserIsBlocked,
    PeerIdInvalid,
    ChannelPrivate,
)
from driver.decorators import sudo_users_only
from driver.database.dbchat import get_served_chats, remove_served_chat
from driver.filters import command, command2


# ═════════════════════════════════════════════
# دوال مساعدة
# ═════════════════════════════════════════════

async def _collect_chats() -> list:
    """يرجّع كل الجروبات المسجّلة (chat_id < 0)."""
    chats = []
    try:
        served = await get_served_chats()
        for chat in served:
            cid = int(chat.get("chat_id", 0))
            if cid < 0:
                chats.append(cid)
    except Exception as e:
        print(f"[broadcast] failed to load chats: {e}")
    return chats


async def _safe_progress_edit(msg: Message, text: str):
    try:
        await msg.edit(text)
    except Exception:
        pass


async def _send_one(c: Client, chat_id: int, mode: str, payload):
    """
    mode:
      - 'text'    -> payload = نص
      - 'forward' -> payload = (from_chat_id, msg_id)
      - 'copy'    -> payload = (from_chat_id, msg_id)
    """
    if mode == "text":
        return await c.send_message(chat_id, payload)
    if mode == "forward":
        from_id, mid = payload
        return await c.forward_messages(chat_id, from_id, mid)
    if mode == "copy":
        from_id, mid = payload
        return await c.copy_message(chat_id, from_id, mid)


async def _broadcast(
    c: Client,
    message: Message,
    *,
    pin: bool = False,
    forward: bool = False,
):
    chats = await _collect_chats()
    if not chats:
        return await message.reply_text("• مفيش جروبات مسجّلة عند البوت لحد دلوقتي.")

    # تحديد طريقة الإرسال
    mode = "text"
    payload = None

    if message.reply_to_message:
        replied = message.reply_to_message
        if forward:
            mode = "forward"
        elif replied.text or replied.caption:
            # نص بسيط — نرسله بنفس البوت
            mode = "text"
            payload = replied.text or replied.caption
        else:
            # وسائط/ستيكر/ميديا — نعمل copy
            mode = "copy"

        if mode in ("forward", "copy"):
            payload = (message.chat.id, replied.id)
    else:
        if len(message.command) < 2:
            return await message.reply_text(
                "**الاستخدام:**\n"
                "• `اذاعه نص الرسالة`\n"
                "• أو رد على رسالة بـ `اذاعه`\n"
                "• `ذت` للإذاعة مع التثبيت\n"
                "• `اذاعه فوروورد` (مع رد) للفوروارد"
            )
        payload = message.text.split(None, 1)[1]
        mode = "text"

    total = len(chats)
    sent = 0
    pinned = 0
    failed = 0
    removed = 0

    status = await message.reply_text(
        f"**📡 جاري بدء الإذاعه...**\n"
        f"• إجمالي الجروبات: `{total}`"
    )
    start = time.time()
    last_edit = 0.0

    for idx, cid in enumerate(chats, 1):
        try:
            sent_msg = await _send_one(c, cid, mode, payload)
            sent += 1
            if pin and sent_msg:
                try:
                    await sent_msg.pin(disable_notification=True)
                    pinned += 1
                except Exception:
                    pass
            await asyncio.sleep(0.25)
        except FloodWait as e:
            await asyncio.sleep(int(getattr(e, "value", 5)) + 1)
            try:
                sent_msg = await _send_one(c, cid, mode, payload)
                sent += 1
                if pin and sent_msg:
                    try:
                        await sent_msg.pin(disable_notification=True)
                        pinned += 1
                    except Exception:
                        pass
            except Exception:
                failed += 1
        except (ChatWriteForbidden, UserIsBlocked, PeerIdInvalid, ChannelPrivate):
            failed += 1
            try:
                await remove_served_chat(cid)
                removed += 1
            except Exception:
                pass
        except Exception:
            failed += 1

        # تحديث شريط التقدم كل ثانية ونص
        now = time.time()
        if now - last_edit >= 1.5 or idx == total:
            last_edit = now
            elapsed = int(now - start)
            await _safe_progress_edit(
                status,
                f"**📡 جاري الإذاعه...**\n"
                f"• تم إرسال: `{sent}` / `{total}`\n"
                f"• فشل: `{failed}`\n"
                f"• ⏱ الوقت: `{elapsed}s`"
            )

    elapsed = int(time.time() - start)
    summary = (
        "**✅ تمت الإذاعه**\n\n"
        f"• تم: `{sent}` جروب\n"
        f"• فشل: `{failed}` جروب\n"
    )
    if pin:
        summary += f"• تم التثبيت في: `{pinned}` جروب\n"
    if removed:
        summary += f"• اتشال من القائمة: `{removed}` (مش موجود/محظور)\n"
    summary += f"• ⏱ الوقت الكلي: `{elapsed}s`"

    try:
        await status.delete()
    except Exception:
        pass
    await message.reply_text(summary)


# ═════════════════════════════════════════════
# الأوامر
# ═════════════════════════════════════════════

@Client.on_message(
    command(["broadcast", "gcast", "اذاعه", "اذاعة"])
    | command2(["اذاعه", "اذاعة", "ذيع"])
)
@sudo_users_only
async def broadcast_cmd(c: Client, message: Message):
    # دعم "اذاعه فوروورد"
    txt = (message.text or "").strip()
    forward = False
    if "فوروورد" in txt or "forward" in txt.lower() or "فورورد" in txt:
        forward = True
    await _broadcast(c, message, pin=False, forward=forward)


@Client.on_message(
    command(["pcast", "pgcast"]) | command2(["ذت", "اذت", "اذع", "اذاعه بالتثبيت"])
)
@sudo_users_only
async def broadcast_pin_cmd(c: Client, message: Message):
    await _broadcast(c, message, pin=True, forward=False)
