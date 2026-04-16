# Copyright (C) 2021 Veez Project

import re
import uuid
import socket
import psutil
import platform
from config import BOT_USERNAME
from driver.filters import command
from pyrogram import Client, filters
from driver.decorators import sudo_users_only, humanbytes


# FETCH SYSINFO

@Client.on_message(command(["sysinfo", f"sysinfo@{BOT_USERNAME}"]))
@sudo_users_only
async def give_sysinfo(client, message):
    await message.delete()
    splatform = platform.system()
    platform_release = platform.release()
    platform_version = platform.version()
    architecture = platform.machine()
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(socket.gethostname())
    mac_address = ":".join(re.findall("..", "%012x" % uuid.getnode()))
    processor = platform.processor()
    ram = humanbytes(round(psutil.virtual_memory().total))
    cpu_freq = psutil.cpu_freq().current
    if cpu_freq >= 1000:
        cpu_freq = f"{round(cpu_freq / 1000, 2)}GHz"
    else:
        cpu_freq = f"{round(cpu_freq, 2)}MHz"
    du = psutil.disk_usage(client.workdir)
    psutil.disk_io_counters()
    disk = f"{humanbytes(du.used)} / {humanbytes(du.total)} " f"({du.percent}%)"
    cpu_len = len(psutil.Process().cpu_affinity())
    somsg = f""" **•• ძᥲᖇᥱძᥱ᥎Ꭵᥣ ••**
┏━━━━━━━━━━━━━━━━━━━━━━━━┓
┣♪ ** :** `{splatform}`
┣♪ **  :** `{platform_release}`
┣♪ **  :** `{platform_version}`
┣♪ ** :** `{architecture}`
┣♪ ** :** `{hostname}`
┣♪ ** :** `{ip_address}`
┣♪ ** :** `{mac_address}`
┣♪ ** :** `{processor}`
┣♪ ** : ** `{ram}`
┣♪ ** :** `{cpu_len}`
┣♪ **  :** `{cpu_freq}`
┣♪ ** :** `{disk}`
┗━━━━━━━━━━━━━━━━━━━━━━━━┛
    """
    await message.reply(somsg)
    