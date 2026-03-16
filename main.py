import asyncio
import subprocess
import os

# ── مسح proxy variables عشان yt-dlp ميتأثرش بـ Railway proxy ──
for _k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
           "ALL_PROXY", "all_proxy", "GLOBAL_AGENT_HTTP_PROXY", "GLOBAL_AGENT_HTTPS_PROXY"]:
    os.environ.pop(_k, None)

from pytgcalls import idle
from pyrogram.errors import FloodWait
from driver.veez import call_py, bot, user

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
from callsmusic import register_stream_end_handler


async def start_bot():
    # معالجة FloodWait عند تشغيل البوت
    while True:
        try:
            await bot.start()
            break
        except FloodWait as e:
            print(f"[WARN]: FloodWait on bot.start() — waiting {e.value}s...")
            await asyncio.sleep(e.value)

    print("[INFO]: BOT CLIENT STARTED !!")

    while True:
        try:
            await user.start()
            break
        except FloodWait as e:
            print(f"[WARN]: FloodWait on user.start() — waiting {e.value}s...")
            await asyncio.sleep(e.value)

    await call_py.start()
    print("[INFO]: PY-TGCALLS CLIENT STARTED !!")

    await register_stream_end_handler(call_py)
    print("[INFO]: STREAM END HANDLER REGISTERED !!")

    if GROUP_SUPPORT:
        try:
            await user.join_chat(GROUP_SUPPORT)
        except FloodWait as e:
            print(f"[WARN]: FloodWait joining GROUP_SUPPORT — waiting {e.value}s...")
            await asyncio.sleep(e.value)
            try:
                await user.join_chat(GROUP_SUPPORT)
            except Exception as e:
                print(f"[WARN]: Could not join GROUP_SUPPORT: {e}")
        except Exception as e:
            print(f"[WARN]: Could not join GROUP_SUPPORT: {e}")

    if UPDATES_CHANNEL:
        try:
            await user.join_chat(UPDATES_CHANNEL)
        except FloodWait as e:
            print(f"[WARN]: FloodWait joining UPDATES_CHANNEL — waiting {e.value}s...")
            await asyncio.sleep(e.value)
            try:
                await user.join_chat(UPDATES_CHANNEL)
            except Exception as e:
                print(f"[WARN]: Could not join UPDATES_CHANNEL: {e}")
        except Exception as e:
            print(f"[WARN]: Could not join UPDATES_CHANNEL: {e}")

    await idle()
    print("[INFO]: STOPPING BOT & USERBOT")
    await bot.stop()


loop = asyncio.get_event_loop()
loop.run_until_complete(start_bot())
