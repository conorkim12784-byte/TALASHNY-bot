"""
Patch to fix:
1. TooOldPyrogramVersion check in py-tgcalls (spoof version)
2. Missing ChatJoinRequest in pyrogram.types
3. Missing pyrogram raw types
"""

# ─── Spoof pyrogram version for py-tgcalls ─────────────────────────────────
try:
    import pyrogram
    pyrogram.__version__ = "1.2.20"
    print(f"[PATCH] Pyrogram version spoofed -> 1.2.20")
except Exception as e:
    print(f"[PATCH] Version spoof warning: {e}")

# ─── Fix missing ChatJoinRequest ───────────────────────────────────────────
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

# ─── Fix missing pyrogram raw types ────────────────────────────────────────
try:
    import pyrogram.raw.types as raw_types
    import pyrogram.errors as errors

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
    if not hasattr(errors, 'GroupcallForbidden'):
        errors.GroupcallForbidden = type('GroupcallForbidden', (Exception,), {})

    print("[PATCH] Pyrogram raw types patched!")
except Exception as e:
    print(f"[PATCH] Raw types warning: {e}")
