from config import API_HASH, API_ID, BOT_TOKEN, SESSION_NAME
from pyrogram import Client
from pytgcalls import PyTgCalls
import os

# SESSION_STRING له الأولوية دائماً — لو مش موجود نستخدم SESSION_NAME كـ fallback
SESSION_STRING = os.getenv("SESSION_STRING", "") or SESSION_NAME

bot = Client(
    ":veez:",
    API_ID,
    API_HASH,
    bot_token=BOT_TOKEN,
    plugins={"root": "program"},
)

# نستخدم session_string فقط — نمنع فتح session file موازي يسبب AUTH_KEY_DUPLICATED
user = Client(
    name="userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
)

call_py = PyTgCalls(user)
