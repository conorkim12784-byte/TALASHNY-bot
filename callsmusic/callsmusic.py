# callsmusic.py — يستخدم call_py من veez مباشرة بدل إنشاء client جديد
from driver.veez import call_py
from . import queues

run = call_py.start
