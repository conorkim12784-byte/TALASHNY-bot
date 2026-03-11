from config import API_HASH, API_ID, BOT_TOKEN, SESSION_NAME
from os import getenv
from pyrogram import Client
from pytgcalls import PyTgCalls

bot = Client(
    ":veez:",
    API_ID,
    API_HASH,
    bot_token=BOT_TOKEN,
    plugins={"root": "program"},
)

# Support SESSION_STRING (pyrogram string session) or SESSION_NAME (file-based)
SESSION_STRING = getenv("SESSION_STRING", "")
if SESSION_STRING:
    user = Client(
        "veez_user",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING,
    )
else:
    user = Client(
        SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
    )

call_py = PyTgCalls(user)
