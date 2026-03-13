# _search_helper.py
# نفس ytsearch اللي في video.py (شغالة) + ytdl_audio بتضيف IGNORE للفيديو

import json
import subprocess
import asyncio


def ytsearch(query: str):
    """
    بحث عبر yt-dlp — نفس الدالة الشغالة في video.py
    بترجع: [title, url, duration, thumbnail]  أو  None لو فشل
    """
    try:
        result = subprocess.run(
            ["yt-dlp", f"ytsearch1:{query}", "--dump-json", "--no-playlist",
             "--no-download", "--no-warnings", "--ignore-errors"],
            capture_output=True, text=True, timeout=60
        )
        if not result.stdout.strip():
            print(f"yt-dlp search error: {result.stderr[:200]}")
            return None
        data = json.loads(result.stdout.strip().split("\n")[0])
        songname = data.get("title", "Unknown")
        url = data.get("webpage_url", "")
        duration_secs = data.get("duration", 0)
        mins, secs = divmod(int(duration_secs), 60)
        duration = f"{mins}:{secs:02d}"
        thumbnail = data.get("thumbnail", "")
        return [songname, url, duration, thumbnail]
    except Exception as e:
        print(e)
        return None


async def ytdl_audio(link: str):
    """
    نفس ytdl في video.py بالظبط — بيجيب stream URL عبر yt-dlp
    بترجع: (1, url) لو نجح  أو  (0, error) لو فشل
    """
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp", "-g", "-f", "bestaudio/best",
        "--no-playlist",
        link,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        return 1, stdout.decode().strip().split("\n")[0]
    else:
        return 0, stderr.decode()
