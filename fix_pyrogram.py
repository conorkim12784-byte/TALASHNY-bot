"""
Patch to fix:
1. Missing pyrogram raw types for old py-tgcalls compatibility
2. msg_id too low / time sync error
Run this before starting the bot
"""
import sys
import types
import time

# ─── Fix Pyrogram session time sync (msg_id too low) ───────────────────────
try:
    from pyrogram.session import Session

    _original_invoke = Session.invoke.__wrapped__ if hasattr(Session.invoke, '__wrapped__') else None

    # Patch the internal time offset in pyrogram session
    # This forces pyrogram to recalculate msg_id based on server time
    try:
        import pyrogram.session.session as _sess_module
        # Override the time_offset to 0 and let it re-sync automatically
        if hasattr(_sess_module, 'Session'):
            original_start = _sess_module.Session.start

            async def patched_start(self):
                # Reset time offset before connecting
                self.server_time_offset = 0
                max_tries = 5
                for i in range(max_tries):
                    try:
                        await original_start(self)
                        break
                    except Exception as e:
                        if "msg_id too low" in str(e) or "synchronized" in str(e):
                            if i < max_tries - 1:
                                import asyncio
                                print(f"[PATCH] msg_id retry {i+1}/{max_tries}...")
                                await asyncio.sleep(3)
                                # Try to reset offset
                                self.server_time_offset = 0
                            else:
                                raise
                        else:
                            raise

            _sess_module.Session.start = patched_start
            print("[PATCH] Session start patched for time sync!")
    except Exception as e:
        print(f"[PATCH] Session patch warning: {e}")

except Exception as e:
    print(f"[PATCH] Time sync patch warning: {e}")

# ─── Fix missing ChatJoinRequest in pyrogram.types ─────────────────────────
try:
    from pyrogram.types import ChatJoinRequest
except ImportError:
    try:
        import pyrogram.types as _ptypes
        from pyrogram import Client as _Client

        class ChatJoinRequest:
            """Fake ChatJoinRequest for pyrogram 1.2.9 compatibility"""
            def __init__(self, *args, **kwargs):
                self.chat = kwargs.get("chat")
                self.from_user = kwargs.get("from_user")
                self.date = kwargs.get("date")

        _ptypes.ChatJoinRequest = ChatJoinRequest

        # Patch on_chat_join_request decorator to do nothing safely
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

# Patch pyrogram.raw.types
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
