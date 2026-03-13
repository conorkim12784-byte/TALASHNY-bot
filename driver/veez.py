import os
from config import API_HASH, API_ID, BOT_TOKEN, SESSION_NAME
from pyrogram import Client
from pytgcalls import PyTgCalls

# الـ SESSION_NAME في .env هي session_string مباشرة (سلسلة طويلة BQA...)
SESSION_STRING = os.getenv("SESSION_STRING") or ""
if not SESSION_STRING and SESSION_NAME and len(SESSION_NAME) > 50:
    SESSION_STRING = SESSION_NAME

if not SESSION_STRING:
    raise ValueError(
        "❌ لم يتم العثور على SESSION_NAME أو SESSION_STRING في .env\n"
        "يجب أن يكون SESSION_NAME = session string صالح (BQA...)"
    )

bot = Client(
    ":veez:",
    API_ID,
    API_HASH,
    bot_token=BOT_TOKEN,
    plugins={"root": "program"},
)

# الـ user client يستخدم session_string مباشرة
user = Client(
    name="talashny_user",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
)

call_py = PyTgCalls(user)
