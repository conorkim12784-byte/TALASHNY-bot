import asyncio

# Fix: Create event loop before importing pytgcalls
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from pyrogram.raw.all import layer  # noqa
from pyrogram import Client
from pytgcalls import idle
from pyrogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
)
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant
from driver.veez import call_py, bot, user
from config import GROUP_SUPPORT, UPDATES_CHANNEL
from callsmusic import register_stream_end_handler


BOT_COMMANDS = [
    BotCommand("start",   "⌁ تشغيل البوت ⌁"),
    BotCommand("help",    "✦ قائمة الأوامر ✦"),
    BotCommand("play",    "▰ تشغيل أغنية ▰"),
    BotCommand("vplay",   "▰ تشغيل فيديو ▰"),
    BotCommand("song",    "⟢ تحميل أغنية ⟢"),
    BotCommand("video",   "⟢ تحميل فيديو ⟢"),
    BotCommand("search",  "✧ بحث في يوتيوب ✧"),
    BotCommand("np",      "♪ المُشغَّل الآن ♪"),
    BotCommand("queue",   "≡ قائمة الانتظار ≡"),
    BotCommand("incall",  "☏ من في الكول ☏"),
    BotCommand("skip",    "» تخطي الأغنية «"),
    BotCommand("pause",   "❚❚ إيقاف مؤقت ❚❚"),
    BotCommand("resume",  "▶ استئناف التشغيل ▶"),
    BotCommand("stop",    "■ إنهاء التشغيل ■"),
    BotCommand("ping",    "⌁ سرعة استجابة البوت ⌁"),
]


async def _set_bot_commands_safe():
    scopes = [
        BotCommandScopeDefault(),
        BotCommandScopeAllPrivateChats(),
        BotCommandScopeAllGroupChats(),
    ]
    for scope in scopes:
        for lang in ("", "ar", "en"):
            try:
                await bot.set_bot_commands(
                    BOT_COMMANDS, scope=scope, language_code=lang
                )
            except Exception as e:
                print(f"[set_bot_commands warn] scope={scope} lang={lang}: {e}")


async def _safe_join(chat_id_or_username: str):
    """ينضم للقناة/الجروب فقط لو الحساب المساعد مش منضم بالفعل،
    عشان البوت ميخرجش ويرجع كل مرة بنشغّله."""
    if not chat_id_or_username:
        return
    try:
        # نحاول نجيب معلومات القناة بحساب المساعد — لو نجح يبقى فعلاً
        # عضو فيها (Telegram بيرجع ChatPreview للأشياء العامة برضو
        # لكن get_chat_member بتاع الميsلف بيتأكد من العضوية)
        me = await user.get_me()
        try:
            member = await user.get_chat_member(chat_id_or_username, me.id)
            status = getattr(member.status, "value", str(member.status)).lower()
            if status in ("member", "administrator", "creator", "owner", "restricted"):
                # موجود بالفعل — متعملش join تاني
                return
        except UserNotParticipant:
            pass
        except Exception:
            # ممكن get_chat_member تفشل لو القناة خاصة وغير منضم —
            # في الحالة دي بنحاول ننضم عادي
            pass

        await user.join_chat(chat_id_or_username)
    except UserAlreadyParticipant:
        return
    except Exception as e:
        print(f"[safe_join warn] {chat_id_or_username}: {e}")


async def start_bot():
    await bot.start()
    print("[INFO]: BOT & UBOT CLIENT STARTED !!")
    await call_py.start()
    print("[INFO]: PY-TGCALLS CLIENT STARTED !!")
    await register_stream_end_handler(call_py)
    print("[INFO]: STREAM END HANDLER REGISTERED !!")
    await _set_bot_commands_safe()
    print("[INFO]: BOT COMMANDS MENU PUBLISHED !!")

    # الانضمام الذكي — لا يعيد الانضمام لو الحساب موجود بالفعل
    await _safe_join(GROUP_SUPPORT)
    await _safe_join(UPDATES_CHANNEL)

    await idle()
    print("[INFO]: STOPPING BOT & USERBOT")
    await bot.stop()


loop.run_until_complete(start_bot())
