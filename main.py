import asyncio
import time
import datetime
from pytgcalls import idle
from driver.veez import call_py, bot, user


async def start_bot():
    # Fix time synchronization issue
    await asyncio.sleep(2)
    await bot.start()
    print("[INFO]: BOT & UBOT CLIENT STARTED !!")
    await call_py.start()
    print("[INFO]: PY-TGCALLS CLIENT STARTED !!")
    try:
        await user.join_chat("Gr_World_Music")
        await user.join_chat("Ch_World_Music")
    except Exception as e:
        print(f"[WARN]: Could not join chats: {e}")
    await idle()
    print("[INFO]: STOPPING BOT & USERBOT")
    await bot.stop()


asyncio.run(start_bot())
