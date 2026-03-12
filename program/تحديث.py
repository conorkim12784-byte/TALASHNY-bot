import os
import sys
import asyncio
import subprocess
from asyncio import sleep
from pyrogram.types import Message
from driver.filters import command2, other_filters
from pyrogram import Client, filters
from os import system, execle, environ
from driver.decorators import sudo_users_only
from config import UPSTREAM_REPO, BOT_USERNAME

# نحاول نستورد git، لو مش موجود نكمل من غيره
try:
    from git import Repo
    from git.exc import InvalidGitRepositoryError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False


def updater():
    if not GIT_AVAILABLE:
        return False
    try:
        from git import Repo
        from git.exc import InvalidGitRepositoryError
        try:
            repo = Repo()
        except InvalidGitRepositoryError:
            return False
        ac_br = repo.active_branch.name
        if "upstream" in repo.remotes:
            ups_rem = repo.remote("upstream")
        else:
            ups_rem = repo.create_remote("upstream", UPSTREAM_REPO)
        ups_rem.fetch(ac_br)
        # شوف لو في commits جديدة
        commits_behind = list(repo.iter_commits(f"HEAD..upstream/{ac_br}"))
        return len(commits_behind) > 0
    except Exception:
        return False


@Client.on_message(command2(["تحديث"]))
@sudo_users_only
async def update_repo(_, message: Message):
    await message.delete()
    msg = await message.reply("🔄 `جاري التحديث...`")
    if not GIT_AVAILABLE:
        return await msg.edit("❌ **git غير متاح على السيرفر**\n\nقم بتثبيته أو تحديث الكود يدوياً.")
    update_avail = updater()
    if update_avail:
        await msg.edit("✅ **تم التحديث**\n\n• جاري إعادة تشغيل البوت...")
        system("git pull -f && pip3 install --no-cache-dir -r requirements.txt")
        execle(sys.executable, sys.executable, "main.py", environ)
        return
    await msg.edit("✅ **البوت محدث بالفعل**", disable_web_page_preview=True)


@Client.on_message(command2(["ريستارت", "اعاده تشغيل"]))
@sudo_users_only
async def restart_bot(_, message: Message):
    await message.delete()
    msg = await message.reply("`جاري إعادة التشغيل...`")
    args = [sys.executable, "main.py"]
    await msg.edit("✅ **تمت إعادة التشغيل**\n\n• البوت جاهز للاستخدام.")
    execle(sys.executable, *args, environ)
    return
