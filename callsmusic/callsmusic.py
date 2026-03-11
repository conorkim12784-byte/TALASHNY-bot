from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import Update, StreamEnded
from config import API_HASH, API_ID, SESSION_NAME

from . import queues

client = Client(SESSION_NAME, API_ID, API_HASH)
pytgcalls = PyTgCalls(client)


@pytgcalls.on_update()
async def on_stream_end(client: PyTgCalls, update: Update) -> None:
    if not isinstance(update, StreamEnded):
        return
    chat_id = update.chat_id
    queues.task_done(chat_id)

    if queues.is_empty(chat_id):
        await pytgcalls.leave_call(chat_id)
    else:
        from pytgcalls.types import MediaStream, AudioQuality
        await pytgcalls.play(
            chat_id,
            MediaStream(
                queues.get(chat_id)["file"],
                audio_parameters=AudioQuality.HIGH,
            ),
        )


run = pytgcalls.start
