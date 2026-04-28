import asyncio

# Fix: Create event loop before importing pytgcalls
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from pytgcalls import idle
from pyrogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
)
from driver.veez import call_py, bot, user
from config import GROUP_SUPPORT, UPDATES_CHANNEL
from callsmusic import register_stream_end_handler


# ═══════════════════════════════════════════════════════
#  قائمة الأوامر التي تظهر فوق صندوق الكتابة في تيليجرام
#  (تظهر دائماً يسار النص لأن واجهة تيليجرام LTR — وكل
#   الأوامر بالعربي بنفس فكرة الزخرفة العامة للبوت)
# ═══════════════════════════════════════════════════════
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
    """ينشر قائمة الأوامر على كل النطاقات (default / private / group)
    وعلى اللغتين الافتراضية والعربية، عشان تظهر بنفس الزخرفة
    لجميع المستخدمين، حتى أصحاب واجهات اللغات الأخرى."""
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


async def start_bot():
    await bot.start()
    print("[INFO]: BOT & UBOT CLIENT STARTED !!")
    await call_py.start()
    print("[INFO]: PY-TGCALLS CLIENT STARTED !!")
    await register_stream_end_handler(call_py)
    print("[INFO]: STREAM END HANDLER REGISTERED !!")
    await _set_bot_commands_safe()
    print("[INFO]: BOT COMMANDS MENU PUBLISHED !!")
    if GROUP_SUPPORT:
        await user.join_chat(GROUP_SUPPORT)
    if UPDATES_CHANNEL:
        await user.join_chat(UPDATES_CHANNEL)
    await idle()
    print("[INFO]: STOPPING BOT & USERBOT")
    await bot.stop()


loop.run_until_complete(start_bot())
