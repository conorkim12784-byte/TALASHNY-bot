"""
Patch to fix:
1. TooOldPyrogramVersion check in py-tgcalls (spoof version)
2. Missing ChatJoinRequest in pyrogram.types
3. Missing pyrogram raw types for old py-tgcalls compatibility
"""
import sys
import types

# ─── Fix TooOldPyrogramVersion: spoof pyrogram version to satisfy py-tgcalls ──
try:
    import pyrogram
    _real_version = pyrogram.__version__
    pyrogram.__version__ = "1.2.20"
    if hasattr(pyrogram, '__version_info__'):
        pyrogram.__version_info__ = (1, 2, 20)
    print(f"[PATCH] Pyrogram version spoofed: {_real_version} -> 1.2.20")
except Exception as e:
    print(f"[PATCH] Version spoof warning: {e}")

# ─── Fix missing ChatJoinRequest in pyrogram.types ─────────────────────────
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

        print("[PATCH] ChatJoinRequest patched successfully!")
    except Exception as e:
        print(f"[PATCH] ChatJoinRequest patch warning: {e}")

# ─── Fix missing pyrogram raw types ────────────────────────────────────────
class UpdateGroupCallConnection:
    ID = 0x2e3a3200
    def __init__(self, *args, **kwargs):
        pass

class GroupCallDiscarded:
    ID = 0x7780bcb4
    def __init__(self, *args, **kwargs):
        pass

class GroupcallForbidden:
    ID = 0x58e40551
    def __init__(self, *args, **kwargs):
        pass

try:
    import pyrogram.raw.types as raw_types
    if not hasattr(raw_types, 'UpdateGroupCallConnection'):
        raw_types.UpdateGroupCallConnection = UpdateGroupCallConnection
    if not hasattr(raw_types, 'GroupCallDiscarded'):
        raw_types.GroupCallDiscarded = GroupCallDiscarded

    import pyrogram.errors as errors
    if not hasattr(errors, 'GroupcallForbidden'):
        errors.GroupcallForbidden = type('GroupcallForbidden', (Exception,), {})

    print("[PATCH] Pyrogram patched successfully!")
except Exception as e:
    print(f"[PATCH] Warning: {e}")
