"""
Patch to fix missing pyrogram raw types for old py-tgcalls compatibility
Run this before starting the bot
"""
import sys
import types

# Create fake UpdateGroupCallConnection class
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
