from config import API_HASH, API_ID, BOT_TOKEN, SESSION_STRING
from pyrogram import Client
from pyrogram.enums import ParseMode
from pytgcalls import PyTgCalls

bot = Client(
    ":veez:",
    API_ID,
    API_HASH,
    bot_token=BOT_TOKEN,
    plugins={"root": "program"},
)

user = Client(
    "assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
)

call_py = PyTgCalls(user)
