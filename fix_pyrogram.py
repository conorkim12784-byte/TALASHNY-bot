"""
Patch to fix:
1. msg_id too low - patch pyrogram session MsgId to use NTP time
2. TooOldPyrogramVersion check in py-tgcalls (spoof version)
3. Missing ChatJoinRequest in pyrogram.types
4. Missing pyrogram raw types for old py-tgcalls compatibility
"""
import sys
import types
import struct
import socket
import time as _time_module

# ─── Step 1: Get real NTP time offset FIRST before anything else ────────────
def _get_ntp_offset():
    servers = ["time.google.com", "time.cloudflare.com", "pool.ntp.org"]
    NTP_DELTA = 2208988800
    for server in servers:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.settimeout(3)
            client.sendto(b'\x1b' + 47 * b'\0', (server, 123))
            data, _ = client.recvfrom(1024)
            client.close()
            if data:
                t = struct.unpack('!12I', data)[10] - NTP_DELTA
                offset = t - int(_time_module.time())
                if abs(offset) > 1:
                    print(f"[PATCH] NTP offset from {server}: {offset}s")
                    return offset
        except Exception:
            continue
    return 0

_ntp_offset = _get_ntp_offset()

# ─── Step 2: Patch time.time() globally so pyrogram uses correct time ───────
if abs(_ntp_offset) > 0:
    _original_time = _time_module.time
    def _corrected_time():
        return _original_time() + _ntp_offset
    _time_module.time = _corrected_time
    print(f"[PATCH] time.time() patched with offset: +{_ntp_offset}s")

# ─── Step 3: Also directly patch pyrogram's MsgId class ────────────────────
try:
    # pyrogram calculates msg_id using time - patch at the source
    import pyrogram.session.internals as _internals
    
    _OrigMsgId = _internals.MsgId
    _orig_time_ref = _time_module.time
    
    class _PatchedMsgId(_OrigMsgId):
        def __new__(cls):
            # Force recalculation with potentially corrected time
            obj = super().__new__(cls)
            return obj
    
    # Alternative: patch the time reference used inside MsgId
    # by replacing the time module reference in internals
    _internals.time = _time_module
    print("[PATCH] MsgId time reference patched!")
    
except Exception as e:
    print(f"[PATCH] MsgId patch warning: {e}")

# ─── Step 4: Patch pyrogram session server_time_offset ─────────────────────
try:
    from pyrogram.session import Session as _Session
    _original_session_start = _Session.start

    async def _patched_session_start(self):
        # Force server_time_offset to our NTP-calculated value
        if hasattr(self, 'server_time_offset'):
            self.server_time_offset = _ntp_offset
        await _original_session_start(self)

    _Session.start = _patched_session_start
    print("[PATCH] Session.start patched with NTP offset!")
except Exception as e:
    print(f"[PATCH] Session patch warning: {e}")

# ─── Step 5: Spoof pyrogram version for py-tgcalls ─────────────────────────
try:
    import pyrogram
    _real_version = pyrogram.__version__
    pyrogram.__version__ = "1.2.20"
    print(f"[PATCH] Pyrogram version spoofed: {_real_version} -> 1.2.20")
except Exception as e:
    print(f"[PATCH] Version spoof warning: {e}")

# ─── Step 6: Fix missing ChatJoinRequest ───────────────────────────────────
try:
    from pyrogram.types import ChatJoinRequest
except ImportError:
    try:
        import pyrogram.types as _ptypes
        from pyrogram import Client as _Client

        class ChatJoinRequest:
            def __init__(self, *args, **kwargs):
                self.chat = kwargs.get("chat")
                self.from_user = kwargs.get("from_user")
                self.date = kwargs.get("date")

        _ptypes.ChatJoinRequest = ChatJoinRequest

        if not hasattr(_Client, "on_chat_join_request"):
            def _on_chat_join_request(*args, **kwargs):
                def decorator(func):
                    return func
                return decorator
            _Client.on_chat_join_request = staticmethod(_on_chat_join_request)

        print("[PATCH] ChatJoinRequest patched!")
    except Exception as e:
        print(f"[PATCH] ChatJoinRequest warning: {e}")

# ─── Step 7: Fix missing pyrogram raw types ─────────────────────────────────
try:
    import pyrogram.raw.types as raw_types

    class UpdateGroupCallConnection:
        ID = 0x2e3a3200
        def __init__(self, *args, **kwargs): pass

    class GroupCallDiscarded:
        ID = 0x7780bcb4
        def __init__(self, *args, **kwargs): pass

    if not hasattr(raw_types, 'UpdateGroupCallConnection'):
        raw_types.UpdateGroupCallConnection = UpdateGroupCallConnection
    if not hasattr(raw_types, 'GroupCallDiscarded'):
        raw_types.GroupCallDiscarded = GroupCallDiscarded

    import pyrogram.errors as errors
    if not hasattr(errors, 'GroupcallForbidden'):
        errors.GroupcallForbidden = type('GroupcallForbidden', (Exception,), {})

    print("[PATCH] Pyrogram raw types patched!")
except Exception as e:
    print(f"[PATCH] Raw types warning: {e}")
