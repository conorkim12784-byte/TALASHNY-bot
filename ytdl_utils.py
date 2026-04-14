# ytdl_utils.py — إعدادات yt-dlp المركزية
# لتجديد الكوكيز: استبدل ملف cookies.txt بس — مش محتاج تعدل أي حاجة تانية

import os

# مسار ملف الكوكيز — موجود في root المشروع
COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")

# ─────────────────────────────────────────
# الـ yt-dlp options الجاهزة
# ─────────────────────────────────────────

def audio_opts(out_tpl: str = "/tmp/%(title)s.%(ext)s") -> dict:
    """Options لتحميل أفضل صوت"""
    return {
        "format": "bestaudio/best",
        "outtmpl": out_tpl,
        "cookiefile": COOKIES_FILE,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
    }


def video_opts(out_tpl: str = "/tmp/%(title)s.%(ext)s", height: int = 720) -> dict:
    """Options لتحميل أفضل فيديو"""
    return {
        "format": f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best",
        "outtmpl": out_tpl,
        "cookiefile": COOKIES_FILE,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
    }


def stream_opts(fmt: str = "bestaudio/best") -> dict:
    """Options لاستخراج رابط مباشر بدون تحميل"""
    return {
        "format": fmt,
        "cookiefile": COOKIES_FILE,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
