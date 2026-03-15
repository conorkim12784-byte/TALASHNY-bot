# FIX: معالجة FloodWait في stream end handler

import os
import asyncio
from pyrogram.errors import FloodWait
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
                if filepath and isinstance(filepath, str) and os.path.exists(filepath):
                    if filepath.startswith("/tmp"):
                        os.remove(filepath)
        except Exception:
            pass

        queues.task_done(chat_id)

        if queues.is_empty(chat_id):
            # مفيش أغاني تانية — اخرج من المكالمة مع معالجة FloodWait
            for attempt in range(3):
                try:
                    await call_py.leave_call(chat_id)
                    break
                except FloodWait as e:
                    print(f"[FloodWait] leave_call: waiting {e.value}s")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    print(f"[leave_call error] {e}")
                    break
        else:
            next_track = queues.get(chat_id)
            if next_track:
                # شغّل الأغنية التالية مع معالجة FloodWait
                for attempt in range(5):
                    try:
                        await call_py.play(
                            chat_id,
                            MediaStream(
                                next_track["file"],
                                audio_parameters=AudioQuality.HIGH,
                                video_flags=MediaStream.Flags.IGNORE,
                            ),
                        )
                        break
                    except FloodWait as e:
                        print(f"[FloodWait] play next track: waiting {e.value}s (attempt {attempt+1})")
                        await asyncio.sleep(e.value)
                    except Exception as e:
                        print(f"[play next track error] {e}")
                        break
