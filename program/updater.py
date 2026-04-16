import os
import sys
import subprocess
from pyrogram import Client
from pyrogram.types import Message
from driver.filters import command
from driver.decorators import sudo_users_only
from config import UPSTREAM_REPO, BOT_USERNAME
from os import execle, environ


def _run(cmd: str) -> tuple[int, str]:
    result = subprocess.run(
        cmd, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    return result.returncode, result.stdout.strip()


def _setup_upstream() -> bool:
    if not UPSTREAM_REPO:
        return False
    if not os.path.exists(".git"):
        _run("git init")
    code, remotes = _run("git remote")
    if "upstream" not in remotes:
        _run(f"git remote add upstream {UPSTREAM_REPO}")
    return True


def check_update() -> tuple[bool, str]:
    if not _setup_upstream():
        return False, "❌ `UPSTREAM_REPO` not set"
    code, out = _run("git fetch upstream")
    if code != 0:
        return False, f"❌ Failed to fetch:\n`{out[:300]}`"
    code2, log = _run("git log HEAD..upstream/main --oneline")
    if code2 != 0:
        code2, log = _run("git log HEAD..upstream/master --oneline")
    if not log.strip():
        return False, "✅ Bot is up-to-date"
    lines = log.strip().split("\n")
    msg = f"🆕 **{len(lines)}** new update(s):\n\n"
    for line in lines[:10]:
        msg += f"• `{line}`\n"
    return True, msg


@Client.on_message(command(["update", f"update@{BOT_USERNAME}"]))
@sudo_users_only
async def update_repo(_, message: Message):
    await message.delete()
    msg = await message.reply("🔄 `Checking for updates...`")
    has_update, info = check_update()
    if not has_update:
        await msg.edit(info)
        return
    await msg.edit(f"{info}\n\n⏳ Updating...")
    code, out = _run("git pull upstream main")
    if code != 0:
        code, out = _run("git pull upstream master")
    if code != 0:
        await msg.edit(f"❌ Update failed:\n`{out[:400]}`")
        return
    _run("pip install --no-cache-dir -r requirements.txt -q")
    await msg.edit("✅ **Updated successfully!**\n\n🔄 Restarting...")
    execle(sys.executable, sys.executable, "main.py", environ)


@Client.on_message(command(["restart", f"restart@{BOT_USERNAME}"]))
@sudo_users_only
async def restart_bot(_, message: Message):
    await message.delete()
    msg = await message.reply("`Restarting...`")
    await msg.edit("✅ **Bot restarted**")
    execle(sys.executable, sys.executable, "main.py", environ)
