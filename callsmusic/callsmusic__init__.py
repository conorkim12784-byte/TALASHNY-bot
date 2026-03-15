# FIX: شلنا export لـ pytgcalls و client القديمين عشان مش محتاجينهم
# دلوقتي بس بنصدّر register_stream_end_handler
from .callsmusic import register_stream_end_handler
from . import queues
