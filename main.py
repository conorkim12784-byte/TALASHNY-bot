import asyncio

# Patch: إصلاح youtube-search-python مع أي إصدار من httpx
try:
    import httpx as _httpx, os as _os, inspect as _inspect
    from youtubesearchpython.core import requests as _ysp_req

    # نكتشف تلقائياً هل httpx بيستخدم proxies أو proxy
    _post_params = list(_inspect.signature(_httpx.post).parameters.keys())
    _use_proxies = 'proxies' in _post_params  # True لـ 0.24، False لـ 0.28

    class _Fixed(_ysp_req.RequestCore):
        def __init__(self):
            self.url = None; self.data = None; self.timeout = 8
            _p = _os.environ.get("HTTP_PROXY") or _os.environ.get("HTTPS_PROXY")
            self._proxy_arg = ({"proxies": {"http://": _p, "https://": _p}} if _p else {}) if _use_proxies else ({"proxy": _p} if _p else {})

        def syncPostRequest(self):
            return _httpx.post(self.url, headers={"User-Agent": "Mozilla/5.0"}, json=self.data, timeout=self.timeout, **self._proxy_arg)

        def syncGetRequest(self):
            return _httpx.get(self.url, headers={"User-Agent": "Mozilla/5.0"}, timeout=self.timeout, cookies={"CONSENT": "YES+1"}, **self._proxy_arg)

        async def asyncPostRequest(self):
            async with _httpx.AsyncClient(**self._proxy_arg) as c:
                return await c.post(self.url, headers={"User-Agent": "Mozilla/5.0"}, json=self.data, timeout=self.timeout)

        async def asyncGetRequest(self):
            async with _httpx.AsyncClient(**self._proxy_arg) as c:
                return await c.get(self.url, headers={"User-Agent": "Mozilla/5.0"}, timeout=self.timeout, cookies={"CONSENT": "YES+1"})

    _ysp_req.RequestCore = _Fixed
    print(f"[PATCH] youtube-search-python patched (httpx={'proxies' if _use_proxies else 'proxy'} mode) ✅")
except Exception as _e:
    print(f"[PATCH] skipped: {_e}")

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
