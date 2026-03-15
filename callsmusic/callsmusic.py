# FIX: استخدام call_py الصحيح + مسح ملفات الفيديو فور انتهاء التشغيل

import os
from pytgcalls.types import Update, StreamEnded, MediaStream, AudioQuality
from . import queues


async def register_stream_end_handler(call_py):

    @call_py.on_update()
    async def on_stream_end(client, update: Update) -> None:
        if not isinstance(update, StreamEnded):
            return

        chat_id = update.chat_id

        # امسح ملف الأغنية اللي خلصت لو كانت ملف محلي في /tmp
        try:
            current = queues.get_current(chat_id)
            if current:
                filepath = current.get("file", "")
                if filepath and filepath.startswith("/tmp") and os.path.exists(filepath):
                    os.remove(filepath)
        except Exception:
            pass

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
                        video_flags=MediaStream.Flags.IGNORE,
                    ),
                )
