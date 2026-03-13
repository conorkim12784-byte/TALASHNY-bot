import asyncio
from pytgcalls import idle
from driver.veez import call_py, bot, user
import driver.utils  # تسجيل stream handlers
from config import GROUP_SUPPORT, UPDATES_CHANNEL


async def start_bot():
    # تشغيل الـ bot client أولاً
    await bot.start()
    # تشغيل الـ user client يدوياً قبل pytgcalls
    await user.start()
    print("[INFO]: BOT & UBOT CLIENT STARTED !!")
    # الآن pytgcalls يستخدم الـ session الشغالة مباشرة
    await call_py.start()
    print("[INFO]: PY-TGCALLS CLIENT STARTED !!")
    if GROUP_SUPPORT:
        try:
            await user.join_chat(GROUP_SUPPORT)
        except Exception as e:
            print(f"[WARN]: Could not join GROUP_SUPPORT: {e}")
    if UPDATES_CHANNEL:
        try:
            await user.join_chat(UPDATES_CHANNEL)
        except Exception as e:
            print(f"[WARN]: Could not join UPDATES_CHANNEL: {e}")
    await idle()
    print("[INFO]: STOPPING BOT & USERBOT")
    await user.stop()
    await bot.stop()


asyncio.run(start_bot())
