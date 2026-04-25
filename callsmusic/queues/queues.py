from typing import Dict
from asyncio import Queue, QueueEmpty as Empty

queues: Dict[int, Queue] = {}
# نحتفظ بالأغنية الحالية لكل شات عشان نقدر نمسح ملفها بعد انتهاء التشغيل
current_tracks: Dict[int, dict] = {}


async def put(chat_id: int, **kwargs) -> int:
    if chat_id not in queues:
        queues[chat_id] = Queue()
    await queues[chat_id].put({**kwargs})
    return queues[chat_id].qsize()


def get(chat_id: int):
    if chat_id in queues:
        try:
            track = queues[chat_id].get_nowait()
            current_tracks[chat_id] = track
            return track
        except Empty:
            return None
    return None


def get_current(chat_id: int):
    return current_tracks.get(chat_id)


def is_empty(chat_id: int) -> bool:
    if chat_id in queues:
        return queues[chat_id].empty()
    return True


def task_done(chat_id: int):
    if chat_id in queues:
        try:
            queues[chat_id].task_done()
        except ValueError:
            pass


def clear(chat_id: int):
    """🔧 إصلاح: الإصدار القديم كان بيرفع Empty حتى لو الـ queue موجودة"""
    if chat_id in queues:
        try:
            # نفرّغ كل العناصر بأمان
            while not queues[chat_id].empty():
                queues[chat_id].get_nowait()
        except Empty:
            pass
        # امسح الـ current track كمان
        current_tracks.pop(chat_id, None)
