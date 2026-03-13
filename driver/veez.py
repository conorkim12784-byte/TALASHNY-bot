from config import API_HASH, API_ID, BOT_TOKEN, SESSION_NAME
from pyrogram import Client
from pytgcalls import PyTgCalls
import os

# SESSION_NAME في الـ .env هي session string (سلسلة طويلة)
# نتحقق: لو هي أطول من 50 حرف → نعاملها كـ session_string
SESSION_STRING = os.getenv("SESSION_STRING", "")
if not SESSION_STRING and SESSION_NAME and len(SESSION_NAME) > 50:
    SESSION_STRING = SESSION_NAME
    _session_name = "talashny_user"
else:
    _session_name = SESSION_NAME if SESSION_NAME and len(SESSION_NAME) <= 50 else "talashny_user"

bot = Client(
    ":veez:",
    API_ID,
    API_HASH,
    bot_token=BOT_TOKEN,
    plugins={"root": "program"},
)

if SESSION_STRING:
    user = Client(
        _session_name,
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING,
    )
else:
    user = Client(
        _session_name,
        api_id=API_ID,
        api_hash=API_HASH,
    )

call_py = PyTgCalls(user)
