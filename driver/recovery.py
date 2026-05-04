"""
نظام الإصلاح التلقائي للحساب المساعد + الدردشة الصوتية.

- Watchdog يفحص الاتصال كل فترة قصيرة.
- لو الحساب المساعد وقع، يعيد تشغيله ويعيد ربط PyTgCalls.
- لو في كول كانت شغالة قبل الكراش، يحاول يرجعها بنفس القائمة.
- يلتقط الـ exceptions اللي بتطلع من pytgcalls (مثل GroupCallNotFound,
  ChatAdminRequired, ConnectionResetError, ... إلخ) ويتعامل معاها.
"""

import asyncio
import traceback
from typing import Dict, List, Any

from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
from pytgcalls.exceptions import NoActiveGroupCall

# AlreadyJoinedError اتشال من الإصدارات الحديثة من pytgcalls.
# بنحاول نستورده، ولو مش موجود بنعرّف Placeholder عشان الكود يفضل شغال.
try:
    from pytgcalls.exceptions import AlreadyJoinedError  # type: ignore
except ImportError:
    class AlreadyJoinedError(Exception):  # type: ignore
        """Fallback: pytgcalls الحديث بيرمي Exception عام بدل ده."""
        pass

from driver.queues import QUEUE, get_queue, clear_queue


# ─── إعدادات ────────────────────────────────────────────────
HEARTBEAT_INTERVAL = 25      # ثواني بين كل فحص
RECOVERY_BACKOFF   = [3, 5, 10, 20, 30]  # تأخير متصاعد بين محاولات الإصلاح

# آخر كولات كانت شغالة (chat_id -> True). بنحتفظ بيها عشان نرجعها بعد الكراش.
ACTIVE_CALLS: Dict[int, bool] = {}


def mark_call_active(chat_id: int) -> None:
    ACTIVE_CALLS[int(chat_id)] = True


def mark_call_inactive(chat_id: int) -> None:
    ACTIVE_CALLS.pop(int(chat_id), None)


def _build_media_stream(item: List[Any]):
    """يبني MediaStream من عنصر الطابور."""
    stream_source = item[1]
    type_   = item[3] if len(item) > 3 else "Audio"
    quality = item[4] if len(item) > 4 else 0

    if type_ == "Video":
        if   quality == 720: vq = VideoQuality.HD_720p
        elif quality == 480: vq = VideoQuality.SD_480p
        elif quality == 360: vq = VideoQuality.SD_360p
        else:                vq = VideoQuality.HD_720p
        return MediaStream(stream_source, AudioQuality.HIGH, vq)

    return MediaStream(
        stream_source,
        audio_parameters=AudioQuality.HIGH,
        audio_flags=MediaStream.Flags.AUTO_DETECT,
        video_flags=MediaStream.Flags.IGNORE,
    )


async def _is_user_alive(user_client) -> bool:
    """يتحقق إن الحساب المساعد لسه متصل."""
    try:
        if not getattr(user_client, "is_connected", False):
            return False
        await asyncio.wait_for(user_client.get_me(), timeout=10)
        return True
    except Exception:
        return False


async def _restart_userbot(user_client, call_py) -> bool:
    """يحاول يعيد تشغيل الحساب المساعد + PyTgCalls."""
    # 1) أوقف pytgcalls لو لسه شغال
    try:
        await call_py.stop()
    except Exception:
        pass

    # 2) أوقف الـ user client
    try:
        if getattr(user_client, "is_connected", False):
            await user_client.stop()
    except Exception:
        pass

    # 3) حاول تشغيل تاني مع backoff
    for delay in RECOVERY_BACKOFF:
        try:
            await user_client.start()
            await call_py.start()
            print("[recovery] ✅ userbot + pytgcalls restarted successfully")
            return True
        except Exception as e:
            print(f"[recovery] ❌ restart failed: {e} — retrying in {delay}s")
            await asyncio.sleep(delay)

    print("[recovery] 🔥 gave up restarting userbot after all retries")
    return False


async def _rejoin_active_calls(call_py) -> None:
    """يحاول يرجع الكولات اللي كانت شغالة قبل الكراش.

    أي chat_id لسه عنده عناصر في QUEUE معناه إن كان فيه كول شغالة،
    فبنحاول نرجّع التشغيل بنفس الأغنية الحالية.
    """
    chat_ids = list(QUEUE.keys()) + list(ACTIVE_CALLS.keys())
    chat_ids = list(set(chat_ids))

    for chat_id in chat_ids:
        chat_queue = get_queue(chat_id)
        if not chat_queue or len(chat_queue) == 0:
            mark_call_inactive(chat_id)
            continue

        try:
            ms = _build_media_stream(chat_queue[0])
            await call_py.play(chat_id, ms)
            mark_call_active(chat_id)
            print(f"[recovery] ▶ rejoined call {chat_id}")
        except AlreadyJoinedError:
            print(f"[recovery] already in call {chat_id}")
        except NoActiveGroupCall:
            print(f"[recovery] no active group call in {chat_id} — clearing")
            clear_queue(chat_id)
            mark_call_inactive(chat_id)
        except Exception as e:
            print(f"[recovery] failed to rejoin {chat_id}: {e}")


async def watchdog(user_client, call_py) -> None:
    """مهمة خلفية تفضل شغالة طول عمر البوت — تفحص وترجّع لو وقع."""
    print("[recovery] 🐕 watchdog started")
    while True:
        try:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            alive = await _is_user_alive(user_client)
            if alive:
                continue

            print("[recovery] ⚠ userbot disconnected — attempting recovery")
            ok = await _restart_userbot(user_client, call_py)
            if ok:
                await _rejoin_active_calls(call_py)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"[recovery] watchdog loop error: {e}")
            traceback.print_exc()
            await asyncio.sleep(5)


def install_global_exception_guard(user_client, call_py) -> None:
    """
    يركّب handler عام على الـ event loop عشان لو حصل أي
    استثناء غير ممسوك في pytgcalls، ميقتلش الحساب المساعد —
    بس يسجّله ويسيب الـ watchdog يصلّح.
    """
    loop = asyncio.get_event_loop()

    def _handler(loop, context):
        msg = context.get("exception") or context.get("message")
        print(f"[recovery] 🛡 caught unhandled loop error: {msg}")
        # متعملش raise — سيب الـ watchdog يكتشف الكراش لو حصل فعلاً.

    loop.set_exception_handler(_handler)
