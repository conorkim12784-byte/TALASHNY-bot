import asyncio
from pytgcalls import idle
from driver.veez import call_py, bot, user
from config import GROUP_SUPPORT, UPDATES_CHANNEL
# FIX: نستورد register_stream_end_handler ونمرر call_py الصحيح ليه
from callsmusic import register_stream_end_handler


async def start_bot():
    await bot.start()
    print("[INFO]: BOT & UBOT CLIENT STARTED !!")
    await user.start()
    await call_py.start()
    print("[INFO]: PY-TGCALLS CLIENT STARTED !!")

    # FIX: نسجل handler الـ stream_end على call_py الصحيح
    await register_stream_end_handler(call_py)
    print("[INFO]: STREAM END HANDLER REGISTERED !!")

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
    await bot.stop()


loop = asyncio.get_event_loop()
loop.run_until_complete(start_bot())
