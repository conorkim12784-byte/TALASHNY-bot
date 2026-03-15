# FIX 1: بدل ما نعمل pytgcalls instance جديد، نستخدم call_py من driver.veez
#         عشان كانوا instance منفصلين وon_stream_end ما كانش بيشتغل صح
# FIX 2: أضفنا video_flags=MediaStream.Flags.IGNORE عشان /play صوت بس

from pytgcalls.types import Update, StreamEnded, MediaStream, AudioQuality
from . import queues


async def register_stream_end_handler(call_py):
    """يتم استدعاء هذه الدالة من main.py لتسجيل الـ handler على call_py الصحيح"""

    @call_py.on_update()
    async def on_stream_end(client, update: Update) -> None:
        if not isinstance(update, StreamEnded):
            return
        chat_id = update.chat_id
        queues.task_done(chat_id)

        if queues.is_empty(chat_id):
            await call_py.leave_call(chat_id)
        else:
            next_track = queues.get(chat_id)
            if next_track:
                await call_py.play(
                    chat_id,
                    MediaStream(
                        next_track["file"],
                        audio_parameters=AudioQuality.HIGH,
                        # FIX 2: صوت بس، بدون فيديو
                        video_flags=MediaStream.Flags.IGNORE,
                    ),
                )
