import fix_pyrogram
import asyncio
import os
import time
import struct
import socket

def sync_time_offset():
    """
    Sync time offset with NTP server manually using Python socket.
    This fixes the Pyrogram 'msg_id too low' error on Railway/cloud servers.
    """
    NTP_SERVER = "time.google.com"
    NTP_PORT = 123
    NTP_DELTA = 2208988800  # seconds between 1900 and 1970

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(5)
        data = b'\x1b' + 47 * b'\0'
        client.sendto(data, (NTP_SERVER, NTP_PORT))
        data, _ = client.recvfrom(1024)
        client.close()

        if data:
            t = struct.unpack('!12I', data)[10]
            t -= NTP_DELTA
            offset = t - int(time.time())
            print(f"[TIME SYNC] Offset from NTP: {offset} seconds")
            return offset
    except Exception as e:
        print(f"[TIME SYNC] Warning: Could not sync with NTP: {e}")
    return 0

# Try system ntpdate first, fallback to Python NTP
os.system("ntpdate -u time.google.com 2>/dev/null || true")
os.system("ntpdate -u pool.ntp.org 2>/dev/null || true")

# Apply Python-level time offset patch for Pyrogram
_time_offset = sync_time_offset()

# Monkey-patch time.time() to compensate for clock skew if needed
if abs(_time_offset) > 2:
    import time as _time_module
    _original_time = _time_module.time
    def _patched_time():
        return _original_time() + _time_offset
    _time_module.time = _patched_time
    print(f"[TIME SYNC] Applied time offset patch: {_time_offset}s")

from pytgcalls import idle
from driver.veez import call_py, bot, user


async def start_bot():
    # Retry logic for connection issues
    max_retries = 5
    for attempt in range(max_retries):
        try:
            await bot.start()
            print("[INFO]: BOT & UBOT CLIENT STARTED !!")
            await call_py.start()
            print("[INFO]: PY-TGCALLS CLIENT STARTED !!")
            await user.join_chat("D_7_k3")
            await user.join_chat("FW_TF")
            await idle()
            print("[INFO]: STOPPING BOT & USERBOT")
            await bot.stop()
            break
        except Exception as e:
            err = str(e)
            if "msg_id too low" in err or "synchronized" in err:
                print(f"[RETRY {attempt+1}/{max_retries}] Time sync error, retrying in 5s... {e}")
                # Re-sync time on each retry
                sync_time_offset()
                await asyncio.sleep(5)
                if attempt == max_retries - 1:
                    raise
            else:
                raise

loop = asyncio.get_event_loop()
loop.run_until_complete(start_bot())
