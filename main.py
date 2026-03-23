import asyncio

# Fix: Create event loop before importing pytgcalls
# pytgcalls sync.py calls asyncio.get_event_loop() at import time,
# which fails in Python 3.10+ if no loop exists in the main thread.
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from pytgcalls import idle
from driver.veez import call_py, bot, user
from config import GROUP_SUPPORT, UPDATES_CHANNEL
from callsmusic import register_stream_end_handler


async def start_bot():
    await bot.start()
    print("[INFO]: BOT & UBOT CLIENT STARTED !!")
    await call_py.start()
    print("[INFO]: PY-TGCALLS CLIENT STARTED !!")
    await register_stream_end_handler(call_py)
    print("[INFO]: STREAM END HANDLER REGISTERED !!")
    if GROUP_SUPPORT:
        await user.join_chat(GROUP_SUPPORT)
    if UPDATES_CHANNEL:
        await user.join_chat(UPDATES_CHANNEL)
    await idle()
    print("[INFO]: STOPPING BOT & USERBOT")
    await bot.stop()


loop.run_until_complete(start_bot())
