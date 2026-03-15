import asyncio
import subprocess
import os
from pytgcalls import idle
from driver.veez import call_py, bot, user

# تثبيت Node.js عشان yt-dlp يقدر يفك تشفير YouTube
def install_nodejs():
    try:
        result = subprocess.run(["node", "--version"], capture_output=True)
        if result.returncode == 0:
            print(f"[INFO]: Node.js already installed: {result.stdout.decode().strip()}")
            return
    except FileNotFoundError:
        pass
    print("[INFO]: Installing Node.js...")
    try:
        subprocess.run(
            "curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs",
            shell=True, check=True
        )
        print("[INFO]: Node.js installed successfully")
    except Exception as e:
        print(f"[WARN]: Could not install Node.js: {e}")

install_nodejs()
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
