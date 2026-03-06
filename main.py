import fix_pyrogram
import asyncio
import os

# Fix time sync issue
os.system("ntpdate -u time.google.com 2>/dev/null || true")

from pytgcalls import idle
from driver.veez import call_py, bot, user


async def start_bot():
    await bot.start()
    print("[INFO]: BOT & UBOT CLIENT STARTED !!")
    await call_py.start()
    print("[INFO]: PY-TGCALLS CLIENT STARTED !!")
    await user.join_chat("D_7_k3")
    await user.join_chat("FW_TF")
    await idle()
    print("[INFO]: STOPPING BOT & USERBOT")
    await bot.stop()

loop = asyncio.get_event_loop()
loop.run_until_complete(start_bot())
