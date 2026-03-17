
from pyrogram.types import Message
from pyrogram import Client
from driver.permissions import get_rank
from config import SUDO_USERS

def sudo_only(func):
    async def wrapper(client:Client, message:Message):
        if message.from_user.id in SUDO_USERS:
            return await func(client,message)
        await message.reply_text("هذا الامر للمطور فقط")
    return wrapper

def owner_only(func):
    async def wrapper(client:Client, message:Message):
        rank = await get_rank(client,message.chat.id,message.from_user.id)
        if rank in ["sudo","owner"]:
            return await func(client,message)
        await message.reply_text("هذا الامر لمالك الجروب")
    return wrapper

def admin_only(func):
    async def wrapper(client:Client, message:Message):
        rank = await get_rank(client,message.chat.id,message.from_user.id)
        if rank in ["sudo","owner","admin"]:
            return await func(client,message)
        await message.reply_text("هذا الامر للمشرفين")
    return wrapper

def everyone(func):
    async def wrapper(client:Client, message:Message):
        return await func(client,message)
    return wrapper
