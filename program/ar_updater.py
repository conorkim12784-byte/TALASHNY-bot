import os
import sys
import subprocess
from pyrogram import Client
from pyrogram.types import Message
from driver.filters import command2
from driver.decorators import sudo_users_only
from config import UPSTREAM_REPO, BOT_USERNAME
from os import execle, environ


def _run(cmd: str) -> tuple[int, str]:
    """تشغيل أمر shell وإرجاع الكود والخرج"""
    result = subprocess.run(
        cmd, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    return result.returncode, result.stdout.strip()


def _is_git_repo() -> bool:
    code, _ = _run("git rev-parse --is-inside-work-tree")
    return code == 0


def _setup_upstream() -> bool:
    """إعداد الـ upstream لو مش موجود"""
    if not UPSTREAM_REPO:
        return False
    # إنشاء git repo لو مش موجود
    if not _is_git_repo():
        _run("git init")
    # إضافة upstream لو مش موجود
    code, remotes = _run("git remote")
    if "upstream" not in remotes:
        _run(f"git remote add upstream {UPSTREAM_REPO}")
    return True


def check_update() -> tuple[bool, str]:
    """التحقق من وجود تحديثات — يرجع (فيه تحديث؟, رسالة)"""
    if not _setup_upstream():
        return False, "❌ `UPSTREAM_REPO` مش محدد في إعدادات البوت"

    code, out = _run("git fetch upstream")
    if code != 0:
        return False, f"❌ فشل الاتصال بالـ repo:\n`{out[:300]}`"

    code2, log = _run("git log HEAD..upstream/main --oneline")
    if code2 != 0:
        # جرب main أو master
        code2, log = _run("git log HEAD..upstream/master --oneline")

    if not log.strip():
        return False, "✅ البوت محدث — لا توجد تحديثات جديدة"

    lines = log.strip().split("\n")
    msg = f"🆕 يوجد **{len(lines)}** تحديث جديد:\n\n"
    for line in lines[:10]:
        msg += f"• `{line}`\n"
    return True, msg


@Client.on_message(command2(["تحديث"]))
@sudo_users_only
async def update_repo(_, message: Message):
    await message.delete()
    msg = await message.reply("🔄 `جاري التحقق من التحديثات...`")

    has_update, info = check_update()

    if not has_update:
        await msg.edit(info)
        return

    await msg.edit(f"{info}\n\n⏳ جاري التحديث...")

    # تحديث الكود
    code, out = _run("git pull upstream main")
    if code != 0:
        code, out = _run("git pull upstream master")

    if code != 0:
        await msg.edit(f"❌ فشل التحديث:\n`{out[:400]}`")
        return

    # تثبيت المكتبات الجديدة
    _run("pip install --no-cache-dir -r requirements.txt -q")

    await msg.edit("✅ **تم التحديث بنجاح!**\n\n🔄 جاري إعادة التشغيل...")

    # إعادة تشغيل البوت
    execle(sys.executable, sys.executable, "main.py", environ)


@Client.on_message(command2(["ريستارت", "اعادة تشغيل", "اعاده تشغيل"]))
@sudo_users_only
async def restart_bot(_, message: Message):
    await message.delete()
    msg = await message.reply("🔄 `جاري إعادة التشغيل...`")
    await msg.edit("✅ **تمت إعادة التشغيل**\n\nالبوت سيكون متاحاً خلال دقيقة.")
    execle(sys.executable, sys.executable, "main.py", environ)
