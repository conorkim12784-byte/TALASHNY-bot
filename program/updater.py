import os
import re
import sys
import asyncio
import subprocess
from asyncio import sleep
from pyrogram.types import Message
from driver.filters import command
from pyrogram import Client, filters
from os import system, execle, environ
from driver.decorators import sudo_users_only
from config import UPSTREAM_REPO, BOT_USERNAME

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
        commits_behind = list(repo.iter_commits(f"HEAD..upstream/{ac_br}"))
        return len(commits_behind) > 0
    except Exception:
        return False


@Client.on_message(command(["update", f"update@{BOT_USERNAME}"]))
@sudo_users_only
async def update_repo(_, message: Message):
    await message.delete()
    msg = await message.reply("🔄 `processing update...`")
    if not GIT_AVAILABLE:
        return await msg.edit("❌ git is not available on this server.")
    update_avail = updater()
    if update_avail:
        await msg.edit("✅ update finished\n\n• bot restarted, back active again in 1 minutes.")
        system("git pull -f && pip3 install --no-cache-dir -r requirements.txt")
        execle(sys.executable, sys.executable, "main.py", environ)
        return
    await msg.edit(f"bot is **up-to-date** ✅", disable_web_page_preview=True)


@Client.on_message(command(["restart", f"restart@{BOT_USERNAME}"]))
@sudo_users_only
async def restart_bot(_, message: Message):
    await message.delete()
    msg = await message.reply("`restarting bot...`")
    args = [sys.executable, "main.py"]
    await msg.edit("✅ bot restarted\n\n• now you can use this bot again.")
    execle(sys.executable, *args, environ)
    return
