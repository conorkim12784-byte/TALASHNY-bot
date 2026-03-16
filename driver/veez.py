from config import API_HASH, API_ID, BOT_TOKEN
from pyrogram import Client
from pytgcalls import PyTgCalls
import os
import sys

# ===== SESSION =====
# البوت يقبل SESSION_NAME أو SESSION_STRING — الاتنين نفس الشيء
# بيدور على أي واحد فيهم وبيستخدمه كـ session_string مباشرة
# لو الاتنين فاضيين — البوت بيوقف ويطلب منك تحط session

_session = (
    os.getenv("SESSION_STRING", "").strip()
    or os.getenv("SESSION_NAME", "").strip()
)

if not _session:
    print("[ERROR]: مفيش SESSION_STRING أو SESSION_NAME في إعدادات البوت!")
    print("[ERROR]: حط الـ session string في متغير SESSION_NAME أو SESSION_STRING")
    sys.exit(1)

# تأكيد إن الـ session string وليس اسم ملف
# session strings دايماً بتبدأ بـ BQ أو 1 وبتكون طويلة +100 حرف
if len(_session) < 50:
    print(f"[ERROR]: SESSION يبدو إنه اسم ملف مش session string: '{_session}'")
    print("[ERROR]: لازم تحط الـ session string الكامل مش اسم ملف")
    sys.exit(1)

# ===== CLIENTS =====
bot = Client(
    name=":veez:",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins={"root": "program"},
)

# الحساب المساعد — session_string فقط، مفيش session file
user = Client(
    name="userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=_session,
)

call_py = PyTgCalls(user)
